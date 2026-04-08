cmake_minimum_required(VERSION 3.8)
project(three_steer_simulation)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  urdf
  launch
  config
  worlds
  scripts
  DESTINATION share/${PROJECT_NAME}/
)

install(PROGRAMS
  scripts/cmd_vel_to_three_steer.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
