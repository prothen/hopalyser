# Hopalyzer

A network hop analyser using async multiprocessed event loop with ZeroMQ and custom MsgPack serialisation.
The node is developed in pure Python with optionally encapsulating ROS wrapper to output connection information about network hop latencies using the message-only `hopalyser_msgs` repository as interface definition.


_Note: [See examplatory use without middleware abstraction for alternative serialisation schemes.](https://stackoverflow.com/questions/43442194/how-do-i-read-and-write-with-msgpack)_


## Usage
Launch the analyzer node with

```bash
roslaunch hopalyser analyzer.launch
```

Request status updates with ping (`status=1`), trace (`status=2`), see `hopalyser_msgs` definition and request with

```bash
rostopic pub /hopalyser_analyzer/request hopalyser_msgs/Status "status: 3" -r 10
```

Output the result under

```bash
rostopic echo /hopalyser_analyzer/status
```

## Setup
Install `mtr` with
```bash
sudo apt-get install -y mtr
```

Fetch Python dependencies using
```bash
pip install -r requirements.txt
```

### ROS interface
Clone this repository into a catkin workspace with
```bash
git clone https://github.com/prothen/hopalyser.git
```
and its message repository with
```bash
git clone https://github.com/prothen/hopalyser_msgs.git
```
build with `catkin build` and source with `source your_catkin_workspace/devel/setup.{sh, zsh}`.


## Contribution
Any contribution is welcome.
If you find missing instructions or something did not work as expected please create an issue and let me know.

## License
See the `LICENSE` file for details of the available open source licensing.
