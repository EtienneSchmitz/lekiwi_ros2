// Agrandit les 6 trous exterieurs (fixation roue) du servo_wheel_hub : M3/M4 -> M5
// Importe le STL d'origine et soustrait des cylindres concentriques. Geometrie preservee.
// Ouvre dans OpenSCAD -> F6 -> File > Export as STL.

hole_d = 5.5;   // Ø M5 passant (5.3 = ajuste, 5.5 = standard, 5.0 = serre)
bc_r   = 23.82; // rayon du cercle de percage (mesure sur la piece)
$fn = 64;

difference() {
    import("servo_wheel_hub.stl");
    // 6 trous a 60 deg (motif hexagonal mesure : 30,90,...,330)
    for (a = [30 : 60 : 330])
        translate([bc_r * cos(a), bc_r * sin(a), -10])
            cylinder(d = hole_d, h = 30);
}
