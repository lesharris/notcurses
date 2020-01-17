from cffi import FFI
ffibuild = FFI()

ffibuild.set_source(
    "_notcurses",
    """
    #include <notcurses.h>
    """,
    libraries=["notcurses"],
)

ffibuild.cdef("""
typedef struct cell {
  // These 32 bits are either a single-byte, single-character grapheme cluster
  // (values 0--0x7f), or an offset into a per-ncplane attached pool of
  // varying-length UTF-8 grapheme clusters. This pool may thus be up to 32MB.
  uint32_t gcluster;          // 1 * 4b -> 4b
  // CELL_STYLE_* attributes (16 bits) + 16 reserved bits
  uint32_t attrword;          // + 4b -> 8b
  // (channels & 0x8000000000000000ull): left half of wide character
  // (channels & 0x4000000000000000ull): foreground is *not* "default color"
  // (channels & 0x3000000000000000ull): foreground alpha (2 bits)
  // (channels & 0x0f00000000000000ull): reserved, must be 0
  // (channels & 0x00ffffff00000000ull): foreground in 3x8 RGB (rrggbb)
  // (channels & 0x0000000080000000ull): right half of wide character
  // (channels & 0x0000000040000000ull): background is *not* "default color"
  // (channels & 0x0000000030000000ull): background alpha (2 bits)
  // (channels & 0x000000000f000000ull): reserved, must be 0
  // (channels & 0x0000000000ffffffull): background in 3x8 RGB (rrggbb)
  // At render time, these 24-bit values are quantized down to terminal
  // capabilities, if necessary. There's a clear path to 10-bit support should
  // we one day need it, but keep things cagey for now. "default color" is
  // best explained by color(3NCURSES). ours is the same concept. until the
  // "not default color" bit is set, any color you load will be ignored.
  uint64_t channels;          // + 8b == 16b
} cell;
typedef enum {
  NCLOGLEVEL_SILENT,  // default. print nothing once fullscreen service begins
  NCLOGLEVEL_PANIC,   // print diagnostics immediately related to crashing
  NCLOGLEVEL_FATAL,   // we're hanging around, but we've had a horrible fault
  NCLOGLEVEL_ERROR,   // we can't keep doin' this, but we can do other things
  NCLOGLEVEL_WARNING, // you probably don't want what's happening to happen
  NCLOGLEVEL_INFO,    // "standard information"
  NCLOGLEVEL_VERBOSE, // "detailed information"
  NCLOGLEVEL_DEBUG,   // this is honestly a bit much
  NCLOGLEVEL_TRACE,   // there's probably a better way to do what you want
} ncloglevel_e;
typedef struct notcurses_options {
  // The name of the terminfo database entry describing this terminal. If NULL,
  // the environment variable TERM is used. Failure to open the terminal
  // definition will result in failure to initialize notcurses.
  const char* termtype;
  // If smcup/rmcup capabilities are indicated, notcurses defaults to making
  // use of the "alternate screen". This flag inhibits use of smcup/rmcup.
  bool inhibit_alternate_screen;
  // By default, we hide the cursor if possible. This flag inhibits use of
  // the civis capability, retaining the cursor.
  bool retain_cursor;
  // Notcurses does not clear the screen on startup unless thus requested to.
  bool clear_screen_start;
  // Notcurses typically prints version info in notcurses_init() and performance
  // info in notcurses_stop(). This inhibits that output.
  bool suppress_banner;
  // We typically install a signal handler for SIG{INT, SEGV, ABRT, QUIT} that
  // restores the screen, and then calls the old signal handler. Set to inhibit
  // registration of these signal handlers.
  bool no_quit_sighandlers;
  // We typically install a signal handler for SIGWINCH that generates a resize
  // event in the notcurses_getc() queue. Set to inhibit this handler.
  bool no_winch_sighandler;
  // If non-NULL, notcurses_render() will write each rendered frame to this
  // FILE* in addition to outfp. This is used primarily for debugging.
  FILE* renderfp;
  // Progressively higher log levels result in more logging to stderr. By
  // default, nothing is printed to stderr once fullscreen service begins.
  ncloglevel_e loglevel;
} notcurses_options;
struct notcurses* notcurses_init(const notcurses_options*, FILE*);
int notcurses_stop(struct notcurses*);
int notcurses_render(struct notcurses*);
struct ncplane* notcurses_stdplane(struct notcurses*);
typedef struct ncinput {
  char32_t id;     // identifier. Unicode codepoint or synthesized NCKEY event
  int y;           // y cell coordinate of event, -1 for undefined
  int x;           // x cell coordinate of event, -1 for undefined
  // FIXME modifiers (alt, etc?)
} ncinput;
int ncplane_set_base(struct ncplane* ncp, const cell* c);
int ncplane_base(struct ncplane* ncp, cell* c);
struct ncplane* notcurses_top(struct notcurses* n);
int notcurses_refresh(struct notcurses* n);
int notcurses_resize(struct notcurses* n, int* y, int* x);
struct ncplane* ncplane_new(struct notcurses* nc, int rows, int cols, int yoff, int xoff, void* opaque);
typedef enum {
  NCALIGN_LEFT,
  NCALIGN_CENTER,
  NCALIGN_RIGHT,
} ncalign_e;
struct ncplane* ncplane_aligned(struct ncplane* n, int rows, int cols, int yoff, ncalign_e align, void* opaque);
unsigned notcurses_supported_styles(const struct notcurses* nc);
int notcurses_palette_size(const struct notcurses* nc);
bool notcurses_canfade(const struct notcurses* nc);
int notcurses_mouse_enable(struct notcurses* n);
int notcurses_mouse_disable(struct notcurses* n);
int ncplane_destroy(struct ncplane* ncp);
bool notcurses_canopen(const struct notcurses* nc);
void ncplane_erase(struct ncplane* n);
int ncplane_cursor_move_yx(struct ncplane* n, int y, int x);
void ncplane_cursor_yx(struct ncplane* n, int* y, int* x);
int ncplane_move_yx(struct ncplane* n, int y, int x);
void ncplane_yx(struct ncplane* n, int* y, int* x);
void ncplane_dim_yx(struct ncplane* n, int* rows, int* cols);
int ncplane_putc_yx(struct ncplane* n, int y, int x, const cell* c);
int ncplane_putsimple_yx(struct ncplane* n, int y, int x, char c);
int ncplane_move_top(struct ncplane* n);
int ncplane_move_bottom(struct ncplane* n);
int ncplane_move_below(struct ncplane* n, struct ncplane* below);
int ncplane_move_above(struct ncplane* n, struct ncplane* above);
struct ncplane* ncplane_below(struct ncplane* n);
char* notcurses_at_yx(struct notcurses* nc, int yoff, int xoff, cell* c);
int ncplane_at_cursor(struct ncplane* n, cell* c);
int ncplane_at_yx(struct ncplane* n, int y, int x, cell* c);
void* ncplane_set_userptr(struct ncplane* n, void* opaque);
void* ncplane_userptr(struct ncplane* n);
int ncplane_resize(struct ncplane* n, int keepy, int keepx, int keepleny,
                       int keeplenx, int yoff, int xoff, int ylen, int xlen);
const void* ncplane_userptr_const(const struct ncplane* n);
uint64_t ncplane_channels(struct ncplane* n);
uint32_t ncplane_attr(struct ncplane* n);
unsigned ncplane_bchannel(struct ncplane* nc);
unsigned ncplane_fchannel(struct ncplane* nc);
unsigned ncplane_fg(struct ncplane* nc);
unsigned ncplane_bg(struct ncplane* nc);
unsigned ncplane_fg_alpha(struct ncplane* nc);
unsigned ncplane_bg_alpha(struct ncplane* nc);
unsigned ncplane_fg_rgb(struct ncplane* n, unsigned* r, unsigned* g, unsigned* b);
unsigned ncplane_bg_rgb(struct ncplane* n, unsigned* r, unsigned* g, unsigned* b);
int ncplane_set_fg_rgb(struct ncplane* n, int r, int g, int b);
int ncplane_set_bg_rgb(struct ncplane* n, int r, int g, int b);
void ncplane_set_fg_rgb_clipped(struct ncplane* n, int r, int g, int b);
void ncplane_set_bg_rgb_clipped(struct ncplane* n, int r, int g, int b);
int ncplane_set_fg(struct ncplane* n, unsigned channel);
int ncplane_set_bg(struct ncplane* n, unsigned channel);
void ncplane_set_fg_default(struct ncplane* n);
void ncplane_set_bg_default(struct ncplane* n);
int ncplane_set_fg_alpha(struct ncplane* n, int alpha);
int ncplane_set_bg_alpha(struct ncplane* n, int alpha);
void ncplane_styles_set(struct ncplane* n, unsigned stylebits);
void ncplane_styles_on(struct ncplane* n, unsigned stylebits);
void ncplane_styles_off(struct ncplane* n, unsigned stylebits);
unsigned ncplane_styles(struct ncplane* n);
typedef struct ncstats {
  uint64_t renders;          // number of successful notcurses_render() runs
  uint64_t failed_renders;   // number of aborted renders, should be 0
  uint64_t render_bytes;     // bytes emitted to ttyfp
  int64_t render_max_bytes;  // max bytes emitted for a frame
  int64_t render_min_bytes;  // min bytes emitted for a frame
  uint64_t render_ns;        // nanoseconds spent in notcurses_render()
  int64_t render_max_ns;     // max ns spent in notcurses_render()
  int64_t render_min_ns;     // min ns spent in successful notcurses_render()
  uint64_t cellelisions;     // cells we elided entirely thanks to damage maps
  uint64_t cellemissions;    // cells we emitted due to inferred damage
  uint64_t fbbytes;          // total bytes devoted to all active framebuffers
  uint64_t fgelisions;       // RGB fg elision count
  uint64_t fgemissions;      // RGB fg emissions
  uint64_t bgelisions;       // RGB bg elision count
  uint64_t bgemissions;      // RGB bg emissions
  uint64_t defaultelisions;  // default color was emitted
  uint64_t defaultemissions; // default color was elided
} ncstats;
void notcurses_stats(struct notcurses* nc, ncstats* stats);
void notcurses_reset_stats(struct notcurses* nc, ncstats* stats);
int ncplane_hline_interp(struct ncplane* n, const cell* c, int len, uint64_t c1, uint64_t c2);
int ncplane_vline_interp(struct ncplane* n, const cell* c, int len, uint64_t c1, uint64_t c2);
int ncplane_box(struct ncplane* n, const cell* ul, const cell* ur, const cell* ll, const cell* lr, const cell* hline, const cell* vline, int ystop, int xstop, unsigned ctlword);
typedef int (*fadecb)(struct notcurses* nc, struct ncplane* ncp);
int ncplane_fadeout(struct ncplane* n, const struct timespec* ts, fadecb fader);
int ncplane_fadein(struct ncplane* n, const struct timespec* ts, fadecb fader);
int ncplane_pulse(struct ncplane* n, const struct timespec* ts, fadecb fader);
int ncplane_putwc_yx(struct ncplane* n, int y, int x, wchar_t w);
int ncplane_putwc(struct ncplane* n, wchar_t w);
int ncplane_putegc_yx(struct ncplane* n, int y, int x, const char* gclust, int* sbytes);
int ncplane_putstr_yx(struct ncplane* n, int y, int x, const char* gclustarr);
int ncplane_putstr_aligned(struct ncplane* n, int y, ncalign_e align, const char* s);
void cell_init(cell* c);
int cell_load(struct ncplane* n, cell* c, const char* gcluster);
int cell_prime(struct ncplane* n, cell* c, const char* gcluster, uint32_t attr, uint64_t channels);
int cell_duplicate(struct ncplane* n, cell* targ, const cell* c);
void cell_release(struct ncplane* n, cell* c);
void cell_styles_set(cell* c, unsigned stylebits);
unsigned cell_styles(const cell* c);
void cell_styles_on(cell* c, unsigned stylebits);
void cell_styles_off(cell* c, unsigned stylebits);
void cell_set_fg_default(cell* c);
void cell_set_bg_default(cell* c);
int cell_set_fg_alpha(cell* c, int alpha);
int cell_set_bg_alpha(cell* c, int alpha);
bool cell_double_wide_p(const cell* c);
bool cell_simple_p(const cell* c);
const char* cell_extended_gcluster(const struct ncplane* n, const cell* c);
bool cell_noforeground_p(const cell* c);
int cell_load_simple(struct ncplane* n, cell* c, char ch);
uint32_t cell_egc_idx(const cell* c);
unsigned cell_bchannel(const cell* cl);
unsigned cell_fchannel(const cell* cl);
uint64_t cell_set_bchannel(cell* cl, uint32_t channel);
uint64_t cell_set_fchannel(cell* cl, uint32_t channel);
uint64_t cell_blend_fchannel(cell* cl, unsigned channel, unsigned blends);
uint64_t cell_blend_bchannel(cell* cl, unsigned channel, unsigned blends);
unsigned cell_fg(const cell* cl);
unsigned cell_bg(const cell* cl);
unsigned cell_fg_alpha(const cell* cl);
unsigned cell_bg_alpha(const cell* cl);
unsigned cell_fg_rgb(const cell* cl, unsigned* r, unsigned* g, unsigned* b);
unsigned cell_bg_rgb(const cell* cl, unsigned* r, unsigned* g, unsigned* b);
int cell_set_fg_rgb(cell* cl, int r, int g, int b);
int cell_set_bg_rgb(cell* cl, int r, int g, int b);
void cell_set_fg_rgb_clipped(cell* cl, int r, int g, int b);
void cell_set_bg_rgb_clipped(cell* cl, int r, int g, int b);
int cell_set_fg(cell* c, uint32_t channel);
int cell_set_bg(cell* c, uint32_t channel);
bool cell_fg_default_p(const cell* cl);
bool cell_bg_default_p(const cell* cl);
typedef struct palette256 {
  // We store the RGB values as a regular ol' channel
  uint32_t chans[256];
} palette256;
palette256* palette256_new(void);
int palette256_use(const palette256* p);
int palette256_set_rgb(palette256* p, int idx, int r, int g, int b);
int palette256_set(palette256* p, int idx, unsigned rgb);
int palette256_get(const palette256* p, int idx, int* r, int* g, int* b);
void palette256_free(palette256* p);
""")

if __name__ == "__main__":
    ffibuild.compile(verbose=True)