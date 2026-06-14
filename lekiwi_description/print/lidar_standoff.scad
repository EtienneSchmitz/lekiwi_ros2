// Entretoise LIDAR (imprimer x4) - cotes en mm
// Relie la base (grille 20 mm) a la plaque support LD06. Vis M3 traversante.
// Ouvre dans OpenSCAD -> F6 -> File > Export as STL.

/* [Geometrie] */
height = 60;   // hauteur de l'entretoise (60 mm pour monter le LIDAR au-dessus du bras)
od     = 8;    // diametre exterieur
id     = 3.2;  // percage M3 (vis qui relie base -> entretoise -> plaque)

$fn = 48;
eps = 0.01;

difference() {
    cylinder(d = od, h = height);
    translate([0, 0, -eps]) cylinder(d = id, h = height + 2*eps);
}
