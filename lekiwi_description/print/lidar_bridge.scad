// Pont support LIDAR LD06 qui ENJAMBE la Raspberry Pi - cotes en mm
// Barre portee par 4 entretoises ; pieds espaces de 7 trous (pas 20 mm = 120 mm)
// pour s'appuyer au-dela de l'emprise du Pi. LIDAR au centre.
// Ouvre dans OpenSCAD -> F6 -> File > Export as STL.

/* [Barre] */
bar_x = 140;   // longueur (pieds a +-60 -> 7 trous, + marge)
bar_y = 50;    // largeur (>= footprint LD06 46.29)
bar_t = 4;     // epaisseur (barre longue -> plus epais = rigide)

/* [Fixation LD06 - datasheet] */
lid_hx     = 46.80;  // entraxe trous X
lid_hy     = 31.92;  // entraxe trous Y
lid_hole_d = 2.7;    // Ø percage (vis M2.5 ; LIDAR = Ø2.5)

/* [Trous de fixation - deux rangees de part et d'autre] */
grid_pitch = 20;   // pas en X (comme la base LeKiwi)
grid_d     = 3.5;  // Ø des trous (M3 passant / standard Open Base)
row_y      = 20;   // ecart des deux rangees par rapport au centre (de part et d'autre)
grid_margin = 6;   // marge mini bord<->centre trou en X

$fn = 64;
eps = 0.01;

// 3 trous du LD06 (centre) -- VERIFIE l'agencement sur ton datasheet
lid_holes = [[-lid_hx/2,  lid_hy/2],
             [ lid_hx/2,  lid_hy/2],
             [ 0,        -lid_hy/2]];

// nombre de trous de part et d'autre du centre (en X), pas grid_pitch
nx = floor((bar_x/2 - grid_margin) / grid_pitch);

difference() {
    linear_extrude(bar_t) square([bar_x, bar_y], center = true);
    // trous LIDAR au centre (motif LD06)
    for (h = lid_holes)
        translate([h[0], h[1], -eps]) cylinder(d = lid_hole_d, h = bar_t + 2*eps);
    // deux rangees de fixation (de part et d'autre), 7 trous chacune au pas grid_pitch
    for (i = [-nx : nx], sy = [-1, 1])
        translate([i*grid_pitch, sy*row_y, -eps])
            cylinder(d = grid_d, h = bar_t + 2*eps);
}
