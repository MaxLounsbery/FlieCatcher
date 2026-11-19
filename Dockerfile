FROM ros:lyrical

WORKDIR /app

COPY . .

RUN colcon build

CMD ros2 run pub fly_catcher
