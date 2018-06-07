#include <stdio.h>

#define u(p) printf("%s\n", p);

void usage()
{
    u("Usage:");
    u("  hw [OPTIONS] PATTERN [PATHS]");
    u("");
    u("The highway searches a PATTERN from all of files under your directory very fast.");
    u("By default hw searches in under your current directory except hidden files and");
    u("paths from .gitignore, but you can search any directories or any files you want");
    u("to search by specifying the PATHS, and you can specified multiple directories or");
    u("files to the PATHS options.");
    u("");
    u("Example:");
    u("  hw hoge src/ include/ tmp/test.txt");
    u("");
    u("Search options:");
    u("  -a, --all-files            Search all files.");
    u("  -e                         Parse PATTERN as a regular expression.");
    u("  -f, --follow-link          Follow symlinks.");
    u("  -i, --ignore-case          Match case insensitively.");
    u("  -w, --word-regexp          Only match whole words.");
    u("");
    u("Output options:");
    u("  -l, --file-with-matches    Only print filenames that contain matches.");
    u("  -n, --line-number          Print line number with output lines.");
    u("  -N, --no-line-number       Don't print line number.");
    u("      --no-omit              Show all characters even if too long lines were matched.");
    u("                             By default hw print only characters near by PATTERN if");
    u("                             the line was too long.");
    u("      --group                Grouping matching lines every files.");
    u("      --no-group             No grouping.");
    u("      --no-buffering         No buffering. By default results is buffering while printing.");
    u("");
    u("Coloring options:");
    u("      --color                Highlight matching strings, filenames, line numbers.");
    u("      --no-color             No highlight.");
    u("      --color-path           Color for path names.");
    u("      --color-match          Color for matching strings.");
    u("      --color-line-number    Color for line numbers.");
    u("      --color-before-context Color for line numbers of the before context.");
    u("      --color-after-context  Color for line numbers of the after context.");
    u("");
    u("Context control:");
    u("  -A, --after-context        Print some lines after match.");
    u("  -B, --before-context       Print some lines before match.");
    u("  -C, --context              Print some lines before and after matches.");
    u("");
    u("  -h, --help                 Show options help and some concept guides.");
    u("      --version              Show version.");
}
