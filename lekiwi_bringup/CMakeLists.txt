cmake_minimum_required(VERSION 3.10...3.27)
project(lekiwi_bringup)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch worlds
  DESTINATION share/${PROJECT_NAME}
)

# Noeud de teleop clavier AZERTY (ZQSD) pour la base holonome
install(
  PROGRAMS scripts/teleop_azerty.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME teleop_azerty
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
