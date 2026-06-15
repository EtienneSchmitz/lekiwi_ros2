cmake_minimum_required(VERSION 3.10...3.27)
project(lekiwi_bringup)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch worlds models
  DESTINATION share/${PROJECT_NAME}
)

# Noeud de teleop clavier AZERTY (ZQSD) pour la base holonome
install(
  PROGRAMS scripts/teleop_azerty.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME teleop_azerty
)

# Spawn d'objets a saisir (Jour 5) + generateur de textures ArUco.
# On conserve l'extension .py : appel via `ros2 run lekiwi_bringup spawn_object.py`.
install(
  PROGRAMS scripts/spawn_object.py scripts/generate_aruco.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
