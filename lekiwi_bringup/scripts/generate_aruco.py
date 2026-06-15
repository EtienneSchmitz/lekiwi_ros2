#!/usr/bin/env python3
"""Genere une (ou plusieurs) image de marqueur ArUco pour le modele aruco_cube.

Les PNG produits sont utilises comme texture (albedo_map) de la face superieure du
cube ArUco (models/aruco_cube/materials/textures/aruco_<id>.png). Quelques IDs sont
deja fournis (0, 1, 2) ; ce script permet d'en (re)generer d'autres.

Dictionnaire : DICT_4X4_50 (suffisant pour un petit nombre de classes ; l'ID = la
classe utilisee par le pick). Bord blanc (quiet zone) inclus pour la detection.

Exemples :
    # regenerer les IDs 0,1,2 dans le dossier du modele
    ros2 run lekiwi_bringup generate_aruco.py
    # un ID precis, taille custom, dossier custom
    ros2 run lekiwi_bringup generate_aruco.py --id 7 --size 512 --out /tmp
"""

import argparse
import os
import sys


def default_out_dir():
    """Dossier textures du modele aruco_cube (source de prefere, sinon share install)."""
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.normpath(os.path.join(
        here, '..', 'models', 'aruco_cube', 'materials', 'textures'))
    return cand


def generate(marker_id, size, border_bits, out_dir):
    try:
        import cv2
        import numpy as np
    except ImportError:
        sys.exit("OpenCV requis : 'sudo apt install python3-opencv' "
                 "(ou pip install opencv-contrib-python).")

    if not hasattr(cv2, 'aruco'):
        sys.exit("Module cv2.aruco absent : installer opencv-contrib-python.")

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    # API OpenCV >= 4.7 : generateImageMarker ; sinon drawMarker.
    if hasattr(cv2.aruco, 'generateImageMarker'):
        marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size)
    else:  # compat anciennes versions
        marker = cv2.aruco.drawMarker(aruco_dict, marker_id, size)

    # Ajout d'une marge blanche (quiet zone) autour du marqueur.
    pad = int(size * 0.12)
    canvas = np.full((size + 2 * pad, size + 2 * pad), 255, dtype=np.uint8)
    canvas[pad:pad + size, pad:pad + size] = marker

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'aruco_{marker_id}.png')
    cv2.imwrite(path, canvas)
    print(f'[generate_aruco] ecrit {path}')


def main():
    p = argparse.ArgumentParser(description='Genere des textures de marqueurs ArUco.')
    p.add_argument('--id', type=int, default=None,
                   help='ID du marqueur (defaut : genere 0,1,2).')
    p.add_argument('--size', type=int, default=512, help='Taille du marqueur en px.')
    p.add_argument('--border-bits', type=int, default=1, help='Largeur bord (bits).')
    p.add_argument('--out', default=None, help='Dossier de sortie.')
    args = p.parse_args()

    out_dir = args.out or default_out_dir()
    ids = [args.id] if args.id is not None else [0, 1, 2]
    for marker_id in ids:
        generate(marker_id, args.size, args.border_bits, out_dir)


if __name__ == '__main__':
    main()
