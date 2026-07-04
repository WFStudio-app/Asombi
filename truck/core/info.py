from utils import err, c, fetch_all_packages, load_installed


def cmd_info(args):
    if not args:
        err("Usage: trk info <package>")
        return

    name = args[0]
    pkgs = fetch_all_packages()
    installed = load_installed()

    pkg = pkgs.get(name)
    if not pkg:
        err(f"Package '{name}' not found.")
        return

    inst   = installed.get(name)
    status = c("green", "Installed") if inst else c("yellow", "Not installed")
    deps   = pkg.get("depends", [])
    deps_str = ", ".join(deps) if deps else "none"

    print(f"""
  {c('bold', 'Package:')}     {c('cyan', name)}
  {c('bold', 'Version:')}     {pkg.get('version', '?')}
  {c('bold', 'Status:')}      {status}
  {c('bold', 'Description:')} {pkg.get('description', 'N/A')}
  {c('bold', 'URL:')}         {pkg.get('url', 'N/A')}
  {c('bold', 'Size:')}        {pkg.get('size', 'unknown')}
  {c('bold', 'Depends:')}     {deps_str}
  {c('bold', 'License:')}     {pkg.get('license', 'unknown')}
""")
