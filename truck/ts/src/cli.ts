#!/usr/bin/env node
/**
 * trk-ts — CLI поверх TypeScript index-модуля Truck.
 *
 * Команды:
 *   trk-ts search <query>        поиск по индексам (+ crates.io fallback)
 *   trk-ts info <package>[@ver]  информация о пакете (резолвер версий)
 *   trk-ts versions <package>    все доступные версии пакета в индексах
 *   trk-ts stats                 размер индексов по репозиториям
 *
 * Установка/сборка остаются за Python-ядром (trk install), т.к. требуют
 * tar/sha256/subprocess-билдов; этот CLI — быстрый read-only фронтend,
 * который позже заменит search/info/repo-list в основном trk.
 */

import {
  DEFAULT_REPOS,
  fetchAllPackages,
  selectVersion,
  resolvePackage,
  searchPackages,
  versionKey,
  compareVersionKeys,
  PackageIndex,
} from "./index";

const args = process.argv.slice(2);
const cmd = args[0];
const rest = args.slice(1);

function fail(msg: string): never {
  console.error(`[trk-ts] ${msg}`);
  process.exit(1);
}

const BOLD = "\x1b[1m", CYAN = "\x1b[96m", GREEN = "\x1b[92m", RESET = "\x1b[0m";

async function main(): Promise<void> {
  if (!cmd || cmd === "help" || cmd === "-h" || cmd === "--help") {
    console.log(`  trk-ts — Truck index core (TypeScript)\n
Usage:
  trk-ts search <query>          Search packages (repos + crates.io fallback)
  trk-ts info <pkg>[@version]    Show package info
  trk-ts versions <pkg>          List all versions available in indexes
  trk-ts stats                   Index size per repository
`);
    return;
  }

  const t0 = Date.now();
  const pkgs: PackageIndex = await fetchAllPackages();
  const ms = Date.now() - t0;
  if (!pkgs.size) fail("Could not fetch any repository index.");

  switch (cmd) {
    case "search": {
      if (!rest.length) fail("Usage: trk-ts search <query>");
      const results = await searchPackages(pkgs, rest.join(" "));
      console.log(`\n${BOLD}Search results for:${RESET} ${CYAN}${rest.join(" ")}${RESET} (${results.length})\n`);
      for (const r of results.slice(0, 40)) {
        const src = r.entry.source === "crates.io" ? " [crates.io]" : "";
        console.log(`  ${BOLD}${r.slug}${RESET} v${r.entry.version ?? "?"}${src}`);
        console.log(`    ${r.entry.description ?? "No description"}\n`);
      }
      break;
    }
    case "info": {
      if (!rest.length) fail("Usage: trk-ts info <package>[@version]");
      const at = rest[0].indexOf("@");
      const name = at < 0 ? rest[0] : rest[0].slice(0, at);
      const wantVer = at < 0 ? "" : rest[0].slice(at + 1);
      const resolved = await resolvePackage(pkgs, name, wantVer || null);
      if (!resolved) fail(`Package '${name}' not found (repositories or crates.io).`);
      const p = resolved.pkg;
      console.log(`
  ${BOLD}Package:${RESET}     ${CYAN}${name}${RESET}
  ${BOLD}Version:${RESET}     ${p.version ?? "?"}
  ${BOLD}Description:${RESET} ${p.description ?? "N/A"}
  ${BOLD}URL:${RESET}         ${p.url ?? "N/A"}
  ${BOLD}Size:${RESET}        ${p.size ?? "unknown"}
  ${BOLD}License:${RESET}     ${p.license ?? "unknown"}
  ${BOLD}SHA256:${RESET}      ${p.sha256 || "(not provided)"}
  ${BOLD}Source:${RESET}      ${resolved.fromCrates ? "crates.io (fallback)" : p.source ?? "repository index"}
`);
      break;
    }
    case "versions": {
      if (!rest.length) fail("Usage: trk-ts versions <package>");
      const name = rest[0];
      const pref = name + "-";
      const list = [...pkgs.entries()]
        .filter(([k, v]) => k.startsWith(pref) && v.name === name)
        .map(([k, v]) => [k, v.version ?? "?"] as const);
      // плюс голая секция Asombi-формата
      if (pkgs.has(name)) list.push([name, pkgs.get(name)!.version ?? "?"]);
      list.sort((a, b) => compareVersionKeys(versionKey(a[1]), versionKey(b[1])));
      console.log(`\n${BOLD}${name}${RESET}: ${list.length} version(s) in indexes\n`);
      for (const [slug, ver] of list.slice(-30)) console.log(`  ${GREEN}v${ver}${RESET}  (${slug})`);
      const [, best] = selectVersion(pkgs, name);
      if (best) console.log(`\n  selected by default: ${BOLD}v${best.version}${RESET}`);
      break;
    }
    case "stats": {
      console.log(`\n${BOLD}Truck index stats${RESET} (${DEFAULT_REPOS.length} repos, fetched in ${ms} ms)\n`);
      const byPkg = new Map<string, number>();
      for (const slug of pkgs.keys()) {
        const base = slug.split(/-(?=\d)/)[0];
        byPkg.set(base, (byPkg.get(base) ?? 0) + 1);
      }
      console.log(`  total entries:   ${pkgs.size}`);
      console.log(`  distinct pkgs:   ${byPkg.size}`);
      for (const [n, cnt] of [...byPkg].sort((a, b) => b[1] - a[1])) {
        console.log(`    ${CYAN}${n.padEnd(14)}${RESET} ${cnt} versions`);
      }
      break;
    }
    default:
      fail(`Unknown command: '${cmd}'. Run 'trk-ts help'.`);
  }
}

main().catch((e) => fail(String(e)));
