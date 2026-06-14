// Plaque support LD06 (a poser sur 4 entretoises imprimees) - cotes en mm
// Dessus = motif de fixation du LD06 (datasheet) ; trous d'angle = entretoises.
// Ouvre dans OpenSCAD -> F6 -> File > Export as STL.

/* [Plaque] */
plate_x = 54.00;   // largeur = footprint LD06 (datasheet)
plate_y = 46.29;   // profondeur = footprint LD06 (datasheet)
plate_t = 3;       // epaisseur

/* [Fixation LD06 - datasheet] */
lid_hx     = 46.80;  // entraxe trous en X
lid_hy     = 31.92;  // entraxe trous en Y
lid_hole_d = 2.7;    // Ø percage (passage vis M2.5 ; LIDAR = Ø2.5)

/* [Fixation sur entretoises] */
mount_pitch = 20;    // grille 20 mm de la base
mount_d     = 3.2;   // Ø passage vis M3 vers les entretoises

/* [Divers] */
cable_d = 0;         // trou central passage cable (0 = aucun)
seat_d  = 0;         // Ø leger lamage pour caler le corps rond du LIDAR (0 = aucun)
seat_h  = 1.0;       // profondeur du lamage

$fn = 72;
eps = 0.01;

// 3 trous du LD06 -- VERIFIE l'agencement exact sur ton datasheet et ajuste si besoin
lid_holes = [[-lid_hx/2,  lid_hy/2],
             [ lid_hx/2,  lid_hy/2],
             [ 0,        -lid_hy/2]];

// 4 entretoises sur la grille 20 mm (sous la plaque) -- aligne sur les trous reels de la base
mount_holes = [[-mount_pitch, -mount_pitch], [ mount_pitch, -mount_pitch],
               [-mount_pitch,  mount_pitch], [ mount_pitch,  mount_pitch]];

difference() {
    linear_extrude(plate_t) square([plate_x, plate_y], center = true);
    // trous LD06
    for (h = lid_holes)
        translate([h[0], h[1], -eps]) cylinder(d = lid_hole_d, h = plate_t + 2*eps);
    // trous entretoises
    for (h = mount_holes)
        translate([h[0], h[1], -eps]) cylinder(d = mount_d, h = plate_t + 2*eps);
    // passage cable central (optionnel)
    if (cable_d > 0)
        translate([0, 0, -eps]) cylinder(d = cable_d, h = plate_t + 2*eps);
    // lamage pour caler le corps rond (optionnel)
    if (seat_d > 0)
        translate([0, 0, plate_t - seat_h]) cylinder(d = seat_d, h = seat_h + eps);
}
