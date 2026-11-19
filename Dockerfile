FROM ros:lyrical

WORKDIR /app

COPY . .

RUN chmod +x start.sh

RUN colcon build

CMD start.sh
