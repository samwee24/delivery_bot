S = {}  # slide id -> (script, transition). Paragraphs are separated by blank lines; line wraps inside a paragraph are ignored.

S['T'] = ("""Good morning, everyone. We're Yujie, Chloe and Sherman, and our project is building an
autonomous driving robot from scratch, on a student budget.""",
"We started with one question.")

S['A'] = ("""This course covered the whole autonomous driving stack, from sensing and localisation to
planning and control. So we asked: how much of it can we build ourselves, cheaply? We had a 2D
lidar, a Raspberry Pi, an IMU, and wheels with motor drivers.""",
"Here's what we built.")

S['R'] = ("""From the top: the round unit on the right is the RPLidar, which spins and measures distance all
around. The Raspberry Pi 4 in the red case runs everything, the small board at the front is the
IMU, and the red board at the back is the motor driver. From the side you can see four DC gear
motors, two per side.

Everything is off the shelf, and there are no wheel encoders, so the robot can't measure how far
its wheels have turned. Keep that in mind, because it shapes most of what follows.""",
"First, let's put this robot next to a real self-driving car.")

S['1.1'] = ("""This Waymo robotaxi carries twenty-nine cameras, plus lidar and radar all around. Ours has one
2D lidar, one IMU and a Raspberry Pi. Yet both run the same loop from the course: build a map,
locate yourself on it, plan a path, and follow it.

The animation shows why that matters even at our scale. In orange is the robot's own motion
estimate over one lap, drifting up to forty-six centimetres. In blue is SLAM, which keeps
correcting it. So the method works. The question is what it takes on hardware this cheap.""",
"Most of that effort went into sensing.")

S['1.2'] = ("""Our lidar scans one flat plane, twelve centimetres off the floor, about seven times a second.
With no encoders, it also has to be our odometry. For that we use rf2o, which compares two
consecutive scans to work out how the robot moved. SLAM Toolbox then builds the map, and later
localises the robot on it.

Three assumptions hide in here, and each comes back later. rf2o assumes nothing in the scene moves.
It treats each scan as a snapshot, though at seven hertz the robot can turn eight degrees mid-sweep.
And it assumes every surface reflects. As the sketch shows, glass often doesn't, and a table top
sits above the plane.""",
"Lidar odometry is weakest on fast turns, which is where the IMU helps.")

S['1.3'] = ("""We combine the two with an Extended Kalman Filter. As the diagram shows, it takes speed and
turning rate from rf2o, turning rate from the gyro, and blends them into one smooth estimate.

The cards show three choices. We fuse speeds, not positions, so one bad reading can't throw it off.
Each input is weighted by its noise, which we measured ourselves. And only the filter may publish
the robot's position. When two programs did, the map visibly spun.""",
"That's how the robot knows where it is. Moving it was just as tricky.")

S['1.4'] = ("""On the left is the motor driver. The speed comes from the duty cycle, the share of time the
power is on. On the right, each side's motors share one channel, so the robot steers like a tank.

The cards are the three catches. With no encoders, it's open loop: we send a duty cycle and trust
the wheels follow. The wheels skid on turns, so real turning differs from the model. And there's a
stall floor: below a certain duty, the wheels don't turn at all.""",
"On top of all this sits the navigation software.")

S['1.5'] = ("""For navigation we use Nav2, the standard ROS 2 package. It plans with Dijkstra's algorithm on a
map where every obstacle is grown by twenty-five centimetres, then follows the path with pure
pursuit, steering at a point just ahead. In our example, the orange band is that margin and the
orange dot is the point being chased.

We capped speed at fifteen centimetres a second, with three safety layers: Nav2's collision
monitor, a lidar stop in our motor program, and a physical switch. Remember that Nav2 slows down
near obstacles. That matters later.""",
"How does our setup compare with published work?")

S['1.6'] = ("""The closest paper, by Kudriashov and colleagues, uses exactly our software. But they recorded
their sensor data and replayed it later on a powerful desktop. When we replayed one of our
recordings on the Pi three times, we got three different distances, all short of what the robot
really moved, because the Pi can't keep up. So everything we show you today was measured live on
the robot.

Merrick and Nandikolla found an IMU cuts odometry error by up to three quarters, which matches our gyro beating the
lidar on turns. Ye and colleagues showed people walking through scans corrupt maps, and we hit that too. And Salem and colleagues describe the mid-sweep smearing from earlier.""",
"And against robots you can buy?")

S['1.7'] = ("""Pudu's BellaBot, a restaurant robot, adds three depth cameras to its lidar and drives up to one
point two metres a second. Starship's sidewalk robot uses cameras and radar. Both see far more
than our single lidar plane, and BellaBot drives eight times faster. Our main gap is clear: we
only see one slice of the room.""",
"I'll hand over to Sherman, who'll show how we built it.")

S['2.1'] = ("""Thanks, Yujie. Here's our software as six blocks: sensing, then odometry and the filter, then
the map, localisation, Nav2, and finally the motors. It all runs on ROS 2.

The orange panel is what we wrote: the IMU and motor programs, the robot description and the
launch files. The blue panel is the existing packages we built on. I'll cover blocks one to five,
and Chloe the motors.""",
"Let's start with the sensors.")

S['3.1'] = ("""Before any mapping, we measured both sensors. On the left is one real scan on our map. The orange
rays found nothing. About a quarter of readings are empty, but the gaps line up with glass and dark
surfaces, not a lidar fault. On the right, a full turn by hand: the gyro read 360.2 degrees, the
lidar odometry 352.9. That's why the filter trusts the gyro for turning.

The filter needed two fixes. The lidar odometry claimed zero uncertainty, so we gave it measured
noise values. And on a busy Pi the filter couldn't keep thirty updates a second, so it runs at
twenty.""",
"With sensors we trusted, we built the map.")

S['3.2'] = ("""We mapped by pushing the robot by hand around a taped loop, about seven minutes, so any error
came from the mapping, not the motors.

The first attempt failed oddly. SLAM Toolbox rejected almost every scan: it expected 931 readings
and got 1041. The driver sent a slightly different count every sweep, the orange line, while SLAM
Toolbox expects it fixed. One driver setting held it at 720, the flat blue line, and the next lap
gave a proper map.""",
"But how good is that map, with nothing to compare it to?")

S['3.3'] = ("""We made our own ground truth. The lap starts and ends on one taped mark, so any gap between
start and end is error. Live, SLAM closed to twenty centimetres, odometry alone was thirty-six off.
The overlay shows the effect: with SLAM, in dark, walls stay thin. With odometry alone, in orange,
they smear and double.

On that map, the robot localises to about three centimetres. But the chart on the right shows a
limit. Start thirty centimetres and twenty degrees off, and it recovers. At thirty-one degrees it
never does, because matching only searches twenty degrees each way. So the robot always starts on
a taped home mark.""",
"Then, partway through, the odometry started giving very wrong answers.")

S['3.4'] = ("""We pushed the robot one metre, and the odometry said twenty-four percent. Same again elsewhere.
It looked like a scaling bug.

These cards follow the investigation. We'd just changed the scan format, but live pushes with
nobody near read a hundred and one and ninety-six percent, so the format was fine. A slow replay
of the bad recording gave the same answer, so it wasn't the Pi being slow either.

What cracked it was counting scan points behind the robot. In the bad pushes, over a hundred sat
half a metre behind, moved with it, and vanished when the push ended. It was the person pushing,
in orange in the animation. rf2o assumes nothing moves, so someone walking behind tells it the
robot is standing still. Ignoring everything within sixty centimetres restored 99.5 percent, so
far on recordings.""",
"With a map and a position we could trust, we handed the robot to Nav2.")

S['3.5'] = ("""Nav2 failed seven ways before reaching one goal. The cards show four.

The first was silent: Nav2 sent commands in one message format, our motor program expected
another, so the wheels never moved and nothing complained. Two came from the slow Pi: timeouts too
short, and position data arriving half a second late, so we relaxed both. The fourth is the stall
floor. Near obstacles, Nav2 slowed to four and a half centimetres a second, below what our wheels
can do, so the robot just stopped.

The other three: the home mark sat too close to furniture, and the robot tried to reverse and spin
at the goal, so we moved the mark and switched those off. Every fix was a setting, not new code.""",
"For the last block, over to Chloe, who'll show what it took to make the wheels obey.")

S['3.6'] = ("""Thanks, Sherman. Early on, the Pi kept rebooting and Nav2 kept shutting down mid-run. So we
logged the Pi's power every two seconds, and these tiles show the result. On the wall supply it
was short of voltage two thirds of the time. On a power bank, zero of sixty samples. A loose motor
wire also rebooted it twice. Until power was stable, no driving result meant anything.""",
"With stable power, we could calibrate the motors.")

S['3.7'] = ("""The first drive was rough: the robot curved up to forty degrees, wouldn't start slowly, and
sometimes overshot two to three times. The Pi generates the motor signal in software, and when it
got busy the timing slipped. Slowing the signal from a thousand to a hundred pulses a second fixed
it.

On the left is our calibration. Speed rises in a line with duty cycle, but below ten centimetres a
second the wheels stall, the same floor that stopped Nav2, so every start gets a short kick. On the
right, two of three one-metre runs landed within ten centimetres, and the flatter lines show the
battery fading.

One more silent failure: the setting that turns the motors live was never passed through, so our
first live runs didn't move.""",
"With all of that in place, here's what the robot did on its own.")

S['3.8'] = ("""We give Nav2 a goal on the far side of a box. The robot plans around it and drives there with
nobody touching it, and after ninety-three seconds Nav2 reports success.

To be upfront: that evening we sent eight goals, and one succeeded. We cancelled the rest as we
found faults. So this proves the whole system works together, but not yet that it's reliable.""",
"Looking back, there's a clear pattern in what went wrong.")

S['3.9'] = ("""We logged fourteen challenges in three weeks. Thirteen came from hardware, the slow computer,
mismatched programs or process, and the bars show cheap hardware alone caused six. Only one, in
coral, came from an algorithm's assumption: the person behind the robot. Eight were surprises.

Two were silent, the message format and the live setting, and the robot just sat there. So our
main takeaway: these packages assume better hardware than ours, and every default had to be
retested.""",
"So what would we do differently?")

S['3.10'] = ("""On the left, five lessons. Integration was the hard part, not the algorithms. Measure physical
limits like stall speed, power and processing load on day one, because each cost us days. Test on
the real robot, not recordings. Without ground truth, design one. And make silent failures loud.

On the right, our limits and next steps: wheel encoders, a hardware motor signal, a faster
computer, and running the people filter live.""",
"So, to close.")

S['Close'] = ("""Back to our question: yes, a low-cost robot can map a room and navigate it on its own, as long
as every physical limit is measured and designed around. Thank you, and we're happy to take
questions.""",
"None.")
