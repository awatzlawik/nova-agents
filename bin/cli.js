#!/usr/bin/env node
/*
 * nova-agents installer — scaffolds the NOVA writing framework into a target folder.
 * Zero dependencies, cross-platform (Windows + macOS + Linux). CommonJS on purpose so it
 * runs the same everywhere without an ESM/loader dance.
 *
 * Usage:
 *   npx nova-agents                         interactive
 *   npx nova-agents --dir . --lang de --name "Anton" --yes   non-interactive
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

// ---------- tiny ANSI helpers (no-ops when not a TTY) ----------
const useColor = process.stdout.isTTY && process.env.NO_COLOR === undefined;
const c = (code) => (s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : String(s));
const bold = c('1');
const dim = c('2');
const cyan = c('36');
const green = c('32');
const yellow = c('33');
const red = c('31');

// ---------- arg parsing ----------
function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--yes' || a === '-y') out.yes = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else if (a === '--version' || a === '-v') out.version = true;
    else if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      if (eq !== -1) out[a.slice(2, eq)] = a.slice(eq + 1);
      else if (i + 1 < argv.length && !argv[i + 1].startsWith('-')) out[a.slice(2)] = argv[++i];
      else out[a.slice(2)] = true;
    } else out._.push(a);
  }
  return out;
}

const STRINGS = {
  de: {
    intro: 'NOVA installieren — autor-zentriertes Schreib-Framework für Claude Code',
    askDir: 'In welchen Ordner installieren?',
    askLang: 'Sprache der Agenten?',
    askName: 'Wie heißt du? (Anrede der Agenten)',
    defaultName: 'Autor',
    copying: 'Kopiere NOVA-Framework',
    wrote: 'Geschrieben',
    done: 'NOVA ist installiert.',
    nextTitle: 'Nächste Schritte',
    next1: 'Öffne den Ordner in Claude Code (oder VS Code mit der Claude-Erweiterung).',
    next2: 'Starte den Dirigenten mit',
    next3: 'Jeder Agent begrüßt dich nun mit deinem Namen und auf Deutsch.',
    settingsSet: 'Sprache und Name in nova/config.yaml gesetzt',
    abort: 'Abgebrochen.',
    overwriteWarn: 'Hinweis: vorhandene NOVA-Dateien in diesem Ordner werden überschrieben.',
    defaultProject: 'mein-roman',
    projectCreated: 'Projektordner angelegt (ohne Beispiel-Dateien):',
    projectExists: 'Hinweis: der Projektordner existiert bereits — Dateien werden ergänzt/überschrieben.',
  },
  en: {
    intro: 'Install NOVA — the author-centric writing framework for Claude Code',
    askDir: 'Install into which folder?',
    askLang: 'Agent language?',
    askName: "What's your name? (how the agents address you)",
    defaultName: 'Author',
    copying: 'Copying NOVA framework',
    wrote: 'Wrote',
    done: 'NOVA is installed.',
    nextTitle: 'Next steps',
    next1: 'Open the folder in Claude Code (or VS Code with the Claude extension).',
    next2: 'Start the conductor with',
    next3: 'Every agent now greets you by name and in English.',
    settingsSet: 'Language and name set in nova/config.yaml',
    abort: 'Aborted.',
    overwriteWarn: 'Note: existing NOVA files in this folder will be overwritten.',
    defaultProject: 'my-novel',
    projectCreated: 'Project folder created (without sample files):',
    projectExists: 'Note: the project folder already exists — files will be merged/overwritten.',
  },
};

function printHelp() {
  console.log(`
${bold('nova-agents')} — install the NOVA writing framework into a folder.

${bold('Usage')}
  npx nova-agents [options]

${bold('Options')}
  --dir <path>      Target folder (default: current directory)
  --lang <de|en>    Agent + document language (default: de)
  --name <name>     Author name the agents greet you with
  --project <name>  Project name — also scaffolds projects/<name>/ (no sample files)
  -y, --yes         Non-interactive: accept defaults / provided flags
  -h, --help        Show this help
  -v, --version     Show version

${bold('Examples')}
  npx nova-agents
  npx nova-agents --project "Mein Roman" --lang de --name "Anton" --yes
  npx nova-agents --dir ./mein-roman --lang de --name "Anton" --yes
  npx github:awatzlawik/nova-agents
`);
}

// ---------- prompt helpers ----------
function makeAsk(rl) {
  return (question, def) =>
    new Promise((resolve) => {
      const suffix = def !== undefined && def !== '' ? dim(` (${def})`) : '';
      rl.question(`${cyan('?')} ${question}${suffix} `, (answer) => {
        const v = answer.trim();
        resolve(v === '' && def !== undefined ? def : v);
      });
    });
}

async function askLang(ask, def) {
  while (true) {
    const v = (await ask(`${STRINGS[def].askLang} [de/en]`, def)).toLowerCase();
    if (v === 'de' || v === 'en') return v;
    console.log(red('  → bitte "de" oder "en" / please enter "de" or "en"'));
  }
}

// Asked first, before the language toggle → bilingual prompt. Loops until non-empty.
async function askProject(ask) {
  while (true) {
    const v = (await ask('Projektname / Project name', '')).trim();
    if (v) return v;
    console.log(red('  → bitte einen Projektnamen eingeben / please enter a project name'));
  }
}

// ---------- yaml scalar patcher (preserves inline comments) ----------
function setYamlScalar(content, key, value) {
  const re = new RegExp(`^(\\s*${key}\\s*:\\s*)(.*?)(\\s*#.*)?$`, 'm');
  if (!re.test(content)) return content;
  return content.replace(re, (_m, p1, _old, comment) => `${p1}${value}${comment || ''}`);
}

function quoteYaml(name) {
  return '"' + String(name).replace(/"/g, "'") + '"';
}

// ---------- recursive copy (merge, overwrite) excluding python cruft ----------
function copyDir(src, dest) {
  fs.cpSync(src, dest, {
    recursive: true,
    force: true,
    filter: (s) => {
      const base = path.basename(s);
      return base !== '__pycache__' && !base.endsWith('.pyc');
    },
  });
}

// ---------- project name → safe folder slug (keeps unicode letters, e.g. umlauts) ----------
function slugifyProject(name) {
  return String(name)
    .trim()
    .replace(/[\/\\]+/g, '-') // path separators → hyphen (never escape the projects/ dir)
    .replace(/\s+/g, '-') // whitespace → hyphen
    .replace(/[^\p{L}\p{N}._-]/gu, '') // drop punctuation, keep letters/digits/._-
    .replace(/-+/g, '-') // collapse repeats
    .replace(/^[-.]+|[-.]+$/g, ''); // trim leading/trailing - and .
}

// ---------- copy the _EXAMPLE skeleton into a fresh project, dropping the sample fixtures ----------
function copyProjectSkeleton(src, dest) {
  fs.cpSync(src, dest, {
    recursive: true,
    force: true,
    filter: (s) => {
      const base = path.basename(s);
      if (base === '__pycache__' || base.endsWith('.pyc')) return false;
      if (base === 'README.md') return false; // _EXAMPLE-only readme (documents the fixtures)
      if (base.startsWith('sample-')) return false; // sample-beat-sheet.json, sample-chapter.md
      return true;
    },
  });
}

function expandHome(p) {
  if (p === '~') return os.homedir();
  if (p.startsWith('~/') || p.startsWith('~\\')) return path.join(os.homedir(), p.slice(2));
  return p;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const pkg = require(path.join(__dirname, '..', 'package.json'));

  if (args.help) return printHelp();
  if (args.version) return console.log(pkg.version);

  const templateDir = path.join(__dirname, '..', 'template');
  if (!fs.existsSync(templateDir)) {
    console.error(red('Internal error: template/ not found next to the installer.'));
    process.exit(1);
  }

  // Defaults
  let lang = (args.lang || 'de').toLowerCase();
  if (lang !== 'de' && lang !== 'en') lang = 'de';
  let targetArg = args.dir || (args._.length ? args._[0] : undefined);
  let name = args.name;

  const interactive = !args.yes && process.stdin.isTTY && process.stdout.isTTY;

  console.log('');
  console.log(bold(cyan('  ◆ NOVA')) + dim('  ·  npx nova-agents v' + pkg.version));
  console.log('  ' + STRINGS[lang].intro);
  console.log('');

  let rl;
  const ask = interactive
    ? makeAsk((rl = readline.createInterface({ input: process.stdin, output: process.stdout })))
    : null;

  try {
    // 1) project name FIRST (bilingual prompt — language not chosen yet)
    let projectName = args.project;
    if (projectName === undefined && interactive) {
      projectName = await askProject(ask);
    }

    // 2) language (localizes every following prompt)
    if (interactive && args.lang === undefined) {
      lang = await askLang(ask, lang);
    }
    const t = STRINGS[lang];

    // fall back to a sensible default when no project name was provided (non-interactive)
    if (projectName === undefined || !String(projectName).trim()) projectName = t.defaultProject;
    const projectSlug = slugifyProject(projectName) || t.defaultProject;

    // 3) target folder
    if (targetArg === undefined) {
      targetArg = interactive ? await ask(t.askDir, process.cwd()) : process.cwd();
    }
    const targetDir = path.resolve(expandHome(targetArg));

    // 4) author name
    if (name === undefined) {
      name = interactive ? await ask(t.askName, t.defaultName) : t.defaultName;
    }
    if (!name) name = t.defaultName;

    if (rl) rl.close();

    // Resolve language words used in the config file (matches the existing style)
    const langWord = lang === 'de' ? 'Deutsch' : 'English';

    console.log('');
    if (fs.existsSync(path.join(targetDir, 'nova', 'config.yaml'))) {
      console.log('  ' + yellow(t.overwriteWarn));
    }
    fs.mkdirSync(targetDir, { recursive: true });

    // Copy framework (nova/, .claude/skills, projects/_EXAMPLE)
    console.log('  ' + dim('… ' + t.copying + ' → ' + targetDir));
    copyDir(templateDir, targetDir);

    // Patch config.yaml with chosen language + author name
    const cfgPath = path.join(targetDir, 'nova', 'config.yaml');
    let cfg = fs.readFileSync(cfgPath, 'utf8');
    cfg = setYamlScalar(cfg, 'communication_language', langWord);
    cfg = setYamlScalar(cfg, 'document_output_language', langWord);
    cfg = setYamlScalar(cfg, 'author_name', quoteYaml(name));
    fs.writeFileSync(cfgPath, cfg);

    // Scaffold the author's own project from the _EXAMPLE skeleton, minus the sample fixtures
    const exampleSrc = path.join(templateDir, 'projects', '_EXAMPLE');
    const projectDest = path.join(targetDir, 'projects', projectSlug);
    let createdProject = false;
    if (projectSlug !== '_EXAMPLE' && fs.existsSync(exampleSrc)) {
      if (fs.existsSync(projectDest)) console.log('  ' + yellow(t.projectExists));
      copyProjectSkeleton(exampleSrc, projectDest);
      createdProject = true;
    }

    // Report
    console.log('  ' + green('✓') + ' ' + t.wrote + ' nova/, .claude/skills/ (23 Agenten), projects/_EXAMPLE/');
    if (createdProject) console.log('  ' + green('✓') + ' ' + t.projectCreated + ' projects/' + projectSlug + '/');
    console.log('  ' + green('✓') + ' ' + t.settingsSet + ` (${langWord}, ${name})`);
    console.log('');
    console.log('  ' + bold(green('✔ ' + t.done)));
    console.log('');
    console.log('  ' + bold(t.nextTitle));
    console.log('    1. ' + t.next1);
    console.log('    2. ' + t.next2 + '  ' + cyan('/nova-orchestrator') + dim('  →  ') + cyan('*plan ' + projectSlug));
    console.log('    3. ' + t.next3);
    console.log('');
  } catch (err) {
    if (rl) rl.close();
    console.error('\n' + red('✗ ') + (err && err.message ? err.message : String(err)));
    process.exit(1);
  }
}

// Graceful Ctrl-C
process.on('SIGINT', () => {
  console.log('\n' + dim('Aborted.'));
  process.exit(130);
});

main();
