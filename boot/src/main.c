#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <dirent.h>
#include <stdarg.h>
#include <errno.h>
#include <time.h>
#include <fcntl.h>

#define VERSION  "0.2.00"
#define BUF      2048
#define CMD_BUF  4096

#define GRN "\033[92m"
#define RED "\033[91m"
#define YEL "\033[93m"
#define CYN "\033[96m"
#define DIM "\033[2m"
#define BLD "\033[1m"
#define RST "\033[0m"

static char g_home[BUF];
static char g_asombi[BUF];
static char g_instances[BUF];
static char g_data[BUF];
static char g_cache[BUF];
static char g_loader[BUF];
static char g_trk[BUF];
static char g_root[BUF];

static void s_ok(const char *m)   { printf("  " GRN "[  OK  ]" RST " %s\n", m); }
static void s_fail(const char *m) { printf("  " RED "[ FAIL ]" RST " %s\n", m); }
static void s_info(const char *m) { printf("  " CYN "[  ..  ]" RST " %s\n", m); }
static void s_warn(const char *m) { printf("  " YEL "[  !!  ]" RST " %s\n", m); }

static int xsnprintf(char *buf, size_t n, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    int r = vsnprintf(buf, n, fmt, ap);
    va_end(ap);
    if (r < 0 || (size_t)r >= n) buf[n-1] = '\0';
    return r;
}

static void init_paths(void) {
    const char *h = getenv("HOME");
    if (!h || !h[0]) { fputs("HOME not set\n", stderr); exit(1); }
    strncpy(g_home, h, BUF - 1);

    xsnprintf(g_asombi,   BUF, "%s/.asombi",            g_home);
    xsnprintf(g_instances, BUF, "%s/.asombi/instances",  g_home);
    xsnprintf(g_data,     BUF, "%s/.asombi/data",        g_home);
    xsnprintf(g_cache,    BUF, "%s/.asombi/cache",       g_home);

    char self[BUF] = {0};
    ssize_t len = readlink("/proc/self/exe", self, BUF - 1);
    if (len > 0) {
        char *s = strrchr(self, '/');
        if (s) { *s = '\0'; s = strrchr(self, '/'); }
        if (s) {
            *s = '\0';
            xsnprintf(g_loader, BUF, "%s/loader-bin/asombi-loader", self);
            xsnprintf(g_trk,    BUF, "%s/bin/trk",                  self);
            xsnprintf(g_root,   BUF, "%s",                          self);
        }
    }
}

static void mkdir_p(const char *path) {
    if (mkdir(path, 0755) != 0 && errno != EEXIST) {
        char m[BUF];
        xsnprintf(m, BUF, "mkdir %s: %s", path, strerror(errno));
        s_warn(m);
    }
}

static void ensure_dirs(void) {
    mkdir_p(g_asombi);
    mkdir_p(g_instances);
    mkdir_p(g_data);
    mkdir_p(g_cache);
}

static int exists(const char *p) {
    struct stat st;
    return stat(p, &st) == 0;
}

static void boot_step(const char *msg) {
    printf("  " DIM "[ .... ]" RST " %s", msg);
    fflush(stdout);
    struct timespec ts = {0, 200000000};
    nanosleep(&ts, NULL);
    printf("\r  " GRN "[  OK  ]" RST " %s\n", msg);
    fflush(stdout);
}

static void banner(void) {
    printf("\n" CYN
    "  \xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88"
    "\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88"
    "\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88"
    "\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88\xe2\x96\x88"
    RST "\n"
    "  Asombi OS v" VERSION " | C Boot | Truck PKG\n\n");
}

static void write_profile(const char *rootfs, const char *name) {
    char path[BUF];
    xsnprintf(path, BUF, "%s/etc/profile", rootfs);
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f,
        "#!/bin/sh\n"
        "export ASOMBI_INSTANCE=\"%s\"\n"
        "export ASOMBI_VERSION=\"" VERSION "\"\n"
        "export TERM=xterm-256color\n"
        "export LANG=en_US.UTF-8\n"
        "export PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        "PS1='\\[\\033[96m\\]asombi\\[\\033[0m\\]@\\[\\033[92m\\]asombi-root"
        "\\[\\033[0m\\]:\\[\\033[93m\\]\\w\\[\\033[0m\\]# '\n"
        "export PS1\n"
        "for _f in /etc/profile.d/*.sh; do [ -r \"$_f\" ] && . \"$_f\"; done\n"
        "unset _f\n"
        "[ -f /root/.asombi/logo.txt ] && cat /root/.asombi/logo.txt\n"
        "echo '  Asombi OS v" VERSION "  |  %s'\n"
        "echo '  trk help - packages  |  exit - logout'\n",
        name, name);
    fclose(f);
}

static void write_resolv(const char *rootfs) {
    char path[BUF];
    xsnprintf(path, BUF, "%s/etc/resolv.conf", rootfs);
    if (exists(path)) return;
    FILE *f = fopen(path, "w");
    if (!f) return;
    fputs("nameserver 8.8.8.8\nnameserver 1.1.1.1\n", f);
    fclose(f);
}

static void install_truck(const char *rootfs) {
    if (!exists(g_trk)) return;

    char dst_dir[BUF], dst[BUF], core_dst[BUF], core_src[BUF], cmd[CMD_BUF];

    xsnprintf(dst_dir,  BUF, "%s/usr/local/bin",  rootfs);
    xsnprintf(dst,      BUF, "%s/trk",             dst_dir);
    xsnprintf(core_dst, BUF, "%s/opt/truck/core",  rootfs);
    xsnprintf(core_src, BUF, "%s/truck/core/.",    g_root);

    mkdir_p(dst_dir);
    xsnprintf(cmd, CMD_BUF, "cp \"%s\" \"%s\" && chmod +x \"%s\"", g_trk, dst, dst);
    if (system(cmd) != 0) { s_warn("Truck binary copy failed"); return; }

    xsnprintf(cmd, CMD_BUF, "mkdir -p \"%s\"", core_dst);
    { int _r = system(cmd); (void)_r; }

    if (exists(core_src)) {
        xsnprintf(cmd, CMD_BUF, "cp -r \"%s\" \"%s/\"", core_src, core_dst);
        { int _r = system(cmd); (void)_r; }
    }

    xsnprintf(cmd, CMD_BUF,
        "sed -i '2i import sys; sys.path.insert(0, \"/opt/truck/core\")' \"%s\"",
        dst);
    { int _r = system(cmd); (void)_r; }
}

static void save_instance_meta(const char *instance_path, const char *name) {
    char path[BUF];
    xsnprintf(path, BUF, "%s/created", instance_path);
    FILE *f = fopen(path, "w");
    if (!f) return;
    time_t now = time(NULL);
    char *ts = ctime(&now);
    fprintf(f, "name=%s\ncreated=%s", name, ts ? ts : "unknown\n");
    fclose(f);
}

static void cmd_login(const char *name) {
    char instance_path[BUF], rootfs[BUF], marker[BUF];

    banner();
    printf("  " BLD "Booting instance:" RST " " CYN "%s" RST "\n\n", name);

    ensure_dirs();

    xsnprintf(instance_path, BUF, "%s/%s",          g_instances, name);
    xsnprintf(rootfs,        BUF, "%s/rootfs",       instance_path);
    xsnprintf(marker,        BUF, "%s/etc/alpine-release", rootfs);

    mkdir_p(instance_path);
    mkdir_p(rootfs);

    if (!exists(marker)) {
        s_info("First boot — downloading Alpine Linux...");

        char arch[64] = "x86_64";
        FILE *fp = popen("uname -m 2>/dev/null", "r");
        if (fp) {
            if (fgets(arch, sizeof(arch), fp))
                arch[strcspn(arch, "\n")] = 0;
            pclose(fp);
        }

        char url[BUF], tarball[BUF], cmd[CMD_BUF];
        const char *base = "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases";
        if (strcmp(arch, "aarch64") == 0)
            xsnprintf(url, BUF, "%s/aarch64/alpine-minirootfs-3.19.0-aarch64.tar.gz", base);
        else
            xsnprintf(url, BUF, "%s/x86_64/alpine-minirootfs-3.19.0-x86_64.tar.gz", base);

        xsnprintf(tarball, BUF, "%s/alpine-%s.tar.gz", g_cache, arch);

        xsnprintf(cmd, CMD_BUF,
            "curl -L --progress-bar -o \"%s\" \"%s\"", tarball, url);
        if (system(cmd) != 0) { s_fail("Download failed"); exit(1); }
        s_ok("Download complete");

        s_info("Extracting rootfs...");
        xsnprintf(cmd, CMD_BUF,
            "tar -xzf \"%s\" -C \"%s\" --no-same-owner 2>/dev/null", tarball, rootfs);
        if (system(cmd) != 0) { s_fail("Extraction failed"); exit(1); }
        remove(tarball);
        s_ok("Alpine rootfs ready");

        boot_step("Configuring Asombi environment");
        write_profile(rootfs, name);
        write_resolv(rootfs);
        install_truck(rootfs);
        boot_step("Installing Truck package manager");
        boot_step("Configuring network DNS");
        save_instance_meta(instance_path, name);
        s_ok("Instance ready");
    } else {
        boot_step("Loading Asombi kernel");
        boot_step("Mounting Alpine filesystem");
        boot_step("Starting session");
    }

    printf("\n  " GRN "✓" RST " Entering Asombi OS — " CYN "%s" RST "\n\n", name);
    fflush(stdout);

    struct timespec ts = {0, 300000000};
    nanosleep(&ts, NULL);

    char termux_bind[BUF];
    xsnprintf(termux_bind, BUF, "%s:/termux-home", g_home);

    if (exists(g_loader)) {
        execl(g_loader, "asombi-loader", rootfs, "/bin/sh", "-l", NULL);
    }

    execlp("proot", "proot",
           "--kill-on-exit",
           "-r", rootfs,
           "-b", "/dev",
           "-b", "/proc",
           "-b", "/sys",
           "-b", termux_bind,
           "-w", "/root",
           "/bin/sh", "-l",
           NULL);

    s_fail("Neither asombi-loader nor proot found");
    exit(1);
}

static void cmd_delete(int argc, char **argv) {
    if (argc == 0) {
        fputs("Usage: os delete <name> | --all | --full\n", stderr);
        return;
    }

    char cmd[CMD_BUF];
    const char *flag = argv[0];

    if (strcmp(flag, "--full") == 0) {
        printf(YEL "  Delete ALL Asombi data: %s\n  Type 'yes': " RST, g_asombi);
        char buf[16] = {0};
        if (fgets(buf, sizeof(buf), stdin) && strncmp(buf, "yes", 3) == 0) {
            xsnprintf(cmd, CMD_BUF, "rm -rf \"%s\"", g_asombi);
            { int _r = system(cmd); (void)_r; }
            s_ok("Asombi OS fully removed");
        } else puts("  Aborted.");
        return;
    }

    if (strcmp(flag, "--all") == 0) {
        printf(YEL "  Delete ALL instances? Type 'yes': " RST);
        char buf[16] = {0};
        if (fgets(buf, sizeof(buf), stdin) && strncmp(buf, "yes", 3) == 0) {
            xsnprintf(cmd, CMD_BUF, "rm -rf \"%s\"/*/", g_instances);
            { int _r = system(cmd); (void)_r; }
            s_ok("All instances deleted");
        } else puts("  Aborted.");
        return;
    }

    char ipath[BUF];
    xsnprintf(ipath, BUF, "%s/%s", g_instances, flag);
    if (!exists(ipath)) {
        printf(RED "  Instance '%s' not found\n" RST, flag);
        return;
    }
    printf(YEL "  Delete instance '%s'? [y/N]: " RST, flag);
    char buf[8] = {0};
    if (fgets(buf, sizeof(buf), stdin) && (buf[0] == 'y' || buf[0] == 'Y')) {
        xsnprintf(cmd, CMD_BUF, "rm -rf \"%s\"", ipath);
        { int _r = system(cmd); (void)_r; }
        printf(GRN "  [  OK  ]" RST " Instance '%s' deleted\n", flag);
    } else puts("  Aborted.");
}

static void cmd_instances(void) {
    DIR *d = opendir(g_instances);
    if (!d) {
        s_info("No instances found");
        printf("  Create: " CYN "os login asombi-1" RST "\n\n");
        return;
    }
    printf("\n  " BLD "Asombi instances:" RST "\n\n");
    struct dirent *e;
    while ((e = readdir(d))) {
        if (e->d_name[0] == '.') continue;
        char meta[BUF];
        xsnprintf(meta, BUF, "%s/%s/created", g_instances, e->d_name);
        char created[64] = "unknown";
        FILE *f = fopen(meta, "r");
        if (f) {
            char line[64];
            while (fgets(line, sizeof(line), f)) {
                if (strncmp(line, "created=", 8) == 0) {
                    strncpy(created, line + 8, sizeof(created) - 1);
                    created[strcspn(created, "\n")] = 0;
                    break;
                }
            }
            fclose(f);
        }
        printf("  " CYN "%-20s" RST " %s\n", e->d_name, created);
    }
    closedir(d);
    printf("\n");
}

static void usage(void) {
    banner();
    printf("  Usage:\n"
           "    " CYN "os login <name>" RST "        Start or create instance\n"
           "    " CYN "os delete <name>" RST "       Delete instance\n"
           "    " CYN "os delete --all" RST "        Delete all instances\n"
           "    " CYN "os delete --full" RST "       Remove all Asombi data\n"
           "    " CYN "os instances" RST "           List all instances\n"
           "    " CYN "os version" RST "             Show version\n\n");
}

int main(int argc, char **argv) {
    init_paths();

    if (argc < 2) { usage(); return 0; }

    const char *cmd = argv[1];

    if      (strcmp(cmd, "login")     == 0) {
        if (argc < 3) { fputs("Usage: os login <name>\n", stderr); return 1; }
        cmd_login(argv[2]);
    }
    else if (strcmp(cmd, "delete")    == 0) cmd_delete(argc - 2, argv + 2);
    else if (strcmp(cmd, "instances") == 0) cmd_instances();
    else if (strcmp(cmd, "version")   == 0)
        puts("  Asombi OS v" VERSION " | Alpine 3.19 | C Boot");
    else {
        fprintf(stderr, "Unknown command: %s\nRun 'os' for help.\n", cmd);
        return 1;
    }

    return 0;
}
