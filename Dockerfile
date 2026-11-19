FROM ros:lyrical

WORKDIR /app

COPY . .

RUN colcon build

RUN . install/setup.bash

CMD ros2 run pub fly_catcher
