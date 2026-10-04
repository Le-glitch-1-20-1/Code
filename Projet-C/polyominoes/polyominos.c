/*
 * Génération de tous les polyominos libres d'ordre n (formes uniques,
 * à rotation/symétrie près, sans tenir compte de la position).
 *
 * Principe : on part du monomino (matrice 1x1). Pour passer de k à k+1 cases,
 * on place chaque forme dans une matrice agrandie de 1 case de chaque côté
 * (h+2 x w+2), on essaie d'ajouter une case à côté d'une case existante,
 * on recadre la matrice, puis on garde la forme canonique parmi les 8
 * rotations/symétries. Une table de hachage élimine les doublons.
 *
 * Sauvegarde : chaque ordre calculé est enregistré dans polyominos_K.txt.
 * Au lancement suivant, le programme recharge le plus grand ordre déjà
 * sauvegardé (<= n) et ne calcule que la suite.
 *
 * Compilation : gcc -O2 -o polyominos polyominos.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int w, h;
    char *c;            /* matrice h x w, c[y*w + x] = 1 si case remplie */
} Poly;

typedef struct {
    Poly *items;
    int n, cap;
    int *head, *next;   /* table de hachage avec chaînage */
    int nb;
} Set;

/* ---------- matrices ---------- */

static Poly poly_new(int w, int h) {
    Poly p = { w, h, calloc((size_t)w * h, 1) };
    return p;
}

static void poly_free(Poly *p) { free(p->c); p->c = NULL; }

/* Recadre la matrice sur la boîte englobante de la forme */
static Poly crop(const Poly *m) {
    int minx = m->w, maxx = -1, miny = m->h, maxy = -1;
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++)
            if (m->c[y * m->w + x]) {
                if (x < minx) minx = x;
                if (x > maxx) maxx = x;
                if (y < miny) miny = y;
                if (y > maxy) maxy = y;
            }
    Poly r = poly_new(maxx - minx + 1, maxy - miny + 1);
    for (int y = 0; y < r.h; y++)
        for (int x = 0; x < r.w; x++)
            r.c[y * r.w + x] = m->c[(y + miny) * m->w + (x + minx)];
    return r;
}

/* Rotation de 90° (sens horaire) */
static Poly rotate(const Poly *p) {
    Poly r = poly_new(p->h, p->w);
    for (int y = 0; y < p->h; y++)
        for (int x = 0; x < p->w; x++)
            r.c[x * r.w + (p->h - 1 - y)] = p->c[y * p->w + x];
    return r;
}

/* Symétrie miroir horizontale */
static Poly flip(const Poly *p) {
    Poly r = poly_new(p->w, p->h);
    for (int y = 0; y < p->h; y++)
        for (int x = 0; x < p->w; x++)
            r.c[y * p->w + (p->w - 1 - x)] = p->c[y * p->w + x];
    return r;
}

static int cmp(const Poly *a, const Poly *b) {
    if (a->w != b->w) return a->w - b->w;
    if (a->h != b->h) return a->h - b->h;
    return memcmp(a->c, b->c, (size_t)a->w * a->h);
}

/* Forme canonique = la plus petite parmi les 8 transformations */
static Poly canonical(const Poly *p) {
    Poly best = poly_new(p->w, p->h);
    memcpy(best.c, p->c, (size_t)p->w * p->h);
    for (int f = 0; f < 2; f++) {
        Poly q = f ? flip(p) : poly_new(p->w, p->h);
        if (!f) memcpy(q.c, p->c, (size_t)p->w * p->h);
        for (int r = 0; r < 4; r++) {
            if (cmp(&q, &best) < 0) {
                poly_free(&best);
                best = poly_new(q.w, q.h);
                memcpy(best.c, q.c, (size_t)q.w * q.h);
            }
            Poly t = rotate(&q);
            poly_free(&q);
            q = t;
        }
        poly_free(&q);
    }
    return best;
}

/* ---------- ensemble (table de hachage) ---------- */

static unsigned hash(const Poly *p) {
    unsigned h = 2166136261u;
    h = (h ^ (unsigned)p->w) * 16777619u;
    h = (h ^ (unsigned)p->h) * 16777619u;
    for (int i = 0; i < p->w * p->h; i++)
        h = (h ^ (unsigned char)p->c[i]) * 16777619u;
    return h;
}

static void set_init(Set *s) {
    s->n = 0; s->cap = 16; s->nb = 16;
    s->items = malloc(sizeof(Poly) * s->cap);
    s->next = malloc(sizeof(int) * s->cap);
    s->head = malloc(sizeof(int) * s->nb);
    for (int i = 0; i < s->nb; i++) s->head[i] = -1;
}

static void set_rehash(Set *s) {
    s->nb *= 2;
    s->head = realloc(s->head, sizeof(int) * s->nb);
    for (int i = 0; i < s->nb; i++) s->head[i] = -1;
    for (int i = 0; i < s->n; i++) {
        unsigned b = hash(&s->items[i]) & (s->nb - 1);
        s->next[i] = s->head[b];
        s->head[b] = i;
    }
}

/* Ajoute p s'il est nouveau (le Set en prend possession), sinon le libère */
static void set_add(Set *s, Poly p) {
    unsigned b = hash(&p) & (s->nb - 1);
    for (int i = s->head[b]; i != -1; i = s->next[i])
        if (cmp(&s->items[i], &p) == 0) { poly_free(&p); return; }
    if (s->n == s->cap) {
        s->cap *= 2;
        s->items = realloc(s->items, sizeof(Poly) * s->cap);
        s->next = realloc(s->next, sizeof(int) * s->cap);
    }
    s->items[s->n] = p;
    s->next[s->n] = s->head[b];
    s->head[b] = s->n++;
    if (s->n > s->nb) set_rehash(s);
}

static void set_free(Set *s) {
    for (int i = 0; i < s->n; i++) poly_free(&s->items[i]);
    free(s->items); free(s->next); free(s->head);
}

/* ---------- génération ---------- */

static void extend(const Poly *p, Set *out) {
    int W = p->w + 2, H = p->h + 2;          /* la matrice grandit */
    Poly big = poly_new(W, H);
    for (int y = 0; y < p->h; y++)
        for (int x = 0; x < p->w; x++)
            big.c[(y + 1) * W + (x + 1)] = p->c[y * p->w + x];

    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            if (big.c[y * W + x]) continue;
            int adj = (y > 0     && big.c[(y - 1) * W + x]) ||
                      (y < H - 1 && big.c[(y + 1) * W + x]) ||
                      (x > 0     && big.c[y * W + x - 1])   ||
                      (x < W - 1 && big.c[y * W + x + 1]);
            if (!adj) continue;
            big.c[y * W + x] = 1;
            Poly cr = crop(&big);
            set_add(out, canonical(&cr));
            poly_free(&cr);
            big.c[y * W + x] = 0;
        }
    poly_free(&big);
}

/* ---------- sauvegarde / chargement ---------- */

static void cache_name(char *buf, size_t sz, int k) {
    snprintf(buf, sz, "polyominos_%d.txt", k);
}

/* Format : première ligne = nombre de formes, puis pour chaque forme
 * "w h" suivi de h lignes de 0/1 (la matrice elle-même). */
static int save_level(int k, const Set *s) {
    char name[64];
    cache_name(name, sizeof name, k);
    FILE *f = fopen(name, "w");
    if (!f) return 0;
    fprintf(f, "%d\n", s->n);
    for (int i = 0; i < s->n; i++) {
        const Poly *p = &s->items[i];
        fprintf(f, "%d %d\n", p->w, p->h);
        for (int y = 0; y < p->h; y++) {
            for (int x = 0; x < p->w; x++)
                fputc('0' + p->c[y * p->w + x], f);
            fputc('\n', f);
        }
    }
    fclose(f);
    return 1;
}

static int load_level(int k, Set *s) {
    char name[64];
    cache_name(name, sizeof name, k);
    FILE *f = fopen(name, "r");
    if (!f) return 0;
    int count;
    if (fscanf(f, "%d", &count) != 1) { fclose(f); return 0; }
    set_init(s);
    for (int i = 0; i < count; i++) {
        int w, h;
        if (fscanf(f, "%d %d", &w, &h) != 2) { fclose(f); set_free(s); return 0; }
        Poly p = poly_new(w, h);
        for (int y = 0; y < h; y++) {
            char line[256];
            if (w >= (int)sizeof line || fscanf(f, "%255s", line) != 1) {
                fclose(f); poly_free(&p); set_free(s); return 0;
            }
            for (int x = 0; x < w; x++) p.c[y * w + x] = line[x] == '1';
        }
        set_add(s, p);
    }
    fclose(f);
    return 1;
}

/* ---------- affichage ---------- */

/* Affiche la vraie matrice de 0 et de 1 */
static void print_poly(const Poly *p) {
    for (int y = 0; y < p->h; y++) {
        printf("| ");
        for (int x = 0; x < p->w; x++)
            printf("%d ", p->c[y * p->w + x]);
        printf("|\n");
    }
    printf("\n");
}

int main(void) {
    int n;
    printf("Ordre n des polyominos : ");
    if (scanf("%d", &n) != 1 || n < 1) {
        fprintf(stderr, "n invalide.\n");
        return 1;
    }

    /* On cherche le plus grand ordre déjà sauvegardé (<= n) */
    Set cur;
    int k0 = 0;
    for (int k = n; k >= 1 && !k0; k--)
        if (load_level(k, &cur)) {
            k0 = k;
            printf("Ordre %d chargé depuis le cache (%d formes).\n", k, cur.n);
        }

    if (!k0) {
        set_init(&cur);
        Poly mono = poly_new(1, 1);
        mono.c[0] = 1;
        set_add(&cur, mono);
        save_level(1, &cur);
        k0 = 1;
    }

    for (int k = k0 + 1; k <= n; k++) {
        Set next;
        set_init(&next);
        for (int i = 0; i < cur.n; i++) extend(&cur.items[i], &next);
        set_free(&cur);
        cur = next;
        save_level(k, &cur);
        printf("Ordre %d calculé : %d formes (sauvegardé).\n", k, cur.n);
    }

    printf("\n%d polyomino(s) libre(s) d'ordre %d.\n", cur.n, n);

    char rep = 'o';
    if (cur.n > 200) {
        printf("Afficher les %d matrices ? (o/n) : ", cur.n);
        if (scanf(" %c", &rep) != 1) rep = 'n';
    }
    if (rep == 'o' || rep == 'O') {
        printf("\n");
        for (int i = 0; i < cur.n; i++) {
            printf("Forme %d/%d (%d x %d) :\n", i + 1, cur.n,
                   cur.items[i].h, cur.items[i].w);
            print_poly(&cur.items[i]);
        }
    }
    printf("Total : %d\n", cur.n);

    set_free(&cur);
    return 0;
}
