# Teacher Lesson Plan: Mapping the School Airwaves

## Lesson Title: Mapping the School's Airwaves (Wireless Networks, GIS, and Data Analytics)
*   **Target Grade Level:** 7th – 9th Grade (Junior High / Middle School)
*   **Subject Focus:** Computer Science, Physics (Waves & Electromagnetism), Math (Averages & Coordinates), and GIS (Geographic Information Systems)
*   **Time Required:** Three 50-minute class periods

---

## 🎯 Learning Objectives
By the end of this lesson, students will be able to:
1.  Explain how Wi-Fi signals travel as radio waves and why obstacles create signal loss (attenuation).
2.  Understand how GPS uses coordinates (latitude, longitude) to place data points on a map.
3.  Perform spatial data collection using the WiGLE mobile app.
4.  Analyze aggregated data in the **Wiggle Mapper** to identify Wi-Fi dead zones and frequency interference.
5.  Formulate data-driven solutions to improve network coverage on campus.

---

## 📚 Standard & Concepts Alignment
*   **Physics:** Electromagnetism, signal amplitude (measured in decibel-milliwatts, dBm), attenuation, and interference.
*   **Mathematics:** Coordinate systems, grid aggregation, calculating averages, and percentages (calculating dead-zone percentage).
*   **Computer Science / Data Literacy:** Data formats (CSV structure, columns, records), data visualization, and troubleshooting network congestion.

---

## 🗓️ Three-Day Curriculum

### Day 1: The Physics of Invisible Waves (Introduction)
*   **Objective:** Understand Wi-Fi, radio waves, signal strength, and prepare for scanning.
*   **Direct Instruction (20 mins):**
    *   What is Wi-Fi? Explain that it uses radio frequency (RF) waves, usually at 2.4 GHz (slower, longer range) or 5 GHz (faster, shorter range).
    *   How do we measure signal strength? Introduce **RSSI** (Received Signal Strength Indicator), measured in **dBm** (decibel-milliwatts).
        *   Show students the scale:
            *   `-30 to -60 dBm` = 🟢 Excellent (fast, stable).
            *   `-61 to -75 dBm` = 🟡 Fair/Weak (slower, web browsing works, but streaming may buffer).
            *   `-76 to -90 dBm` = 🔴 Poor/Dead Zone (frequent disconnects, no usable internet).
    *   Explain **Interference**: Imagine a room where 10 people are talking loudly at the same time on the same pitch. That is what happens when too many routers share the same Wi-Fi channel (e.g., Channel 6).
*   **Activity (20 mins):**
    *   Assist students in downloading and setting up the **WiGLE Wi-Fi** app (following the [Student Guide](file:///home/leifdavisson/wiggle_mapper/docs/student_guide.md)).
    *   Split the class into mapping teams and assign each team a specific quadrant of the school campus (e.g., Team A: Gym/Cafeteria, Team B: Science Wing, Team C: Courtyard).
*   **Wrap-up (10 mins):**
    *   Q&A. Remind students to charge their phones for the next day's campaign.

---

### Day 2: The Great Campus Scan (Data Gathering)
*   **Objective:** Execute the data collection campaign.
*   **Setup (10 mins):**
    *   Review the safety and boundary rules.
    *   Have students open the WiGLE app and verify that GPS and Scanning are running.
*   **Field Work (30 mins):**
    *   Send student teams to their assigned quadrants to walk and scan.
    *   *Teacher tip:* Walk with students to ensure they are walking slowly, keeping their devices exposed, and covering rooms systematically.
*   **Wrap-up & Export (10 mins):**
    *   Return to the classroom.
    *   Have students stop their scans, export their WiGLE data as CSV files, and submit them to your class portal (Google Classroom, shared drive, or email).

---

### Day 3: Analyzing the Invisible Map (Data Analysis & Career Connect)
*   **Objective:** Upload and analyze the data, identify problems, and brainstorm solutions.
*   **Map Visualization (20 mins):**
    *   Open the **Wiggle Mapper** on a projector.
    *   Drag and drop all student CSV files into the upload zone to merge them.
    *   Type the school’s main Wi-Fi network name (SSID) into the filter box.
    *   Draw the school boundary using the drawing tool.
    *   **Analyze the Overlays together:**
        *   **Raw Points:** See where students walked.
        *   **Grid Overlay:** Find the cells colored red or yellow. Where are the weak spots?
        *   **Needs More Data (Pink Overlay):** Point out any spaces that are pink. Ask: *"Why did we miss this room? Did the signal fail, or did no one walk there?"*
        *   **Channel Congestion Chart:** Look at the bar chart. Are there 15 networks competing on Channel 11? Is there interference?
*   **Group Discussion / Problem Solving (15 mins):**
    *   Ask students to write down:
        1. Where is the worst dead zone on campus?
        2. What channel is the most crowded?
        3. Propose two fixes (e.g., adding an Access Point, moving an AP away from metal lockers, changing the channel of a router).
*   **Career Connections (15 mins):** Explain how these activities relate to real-world jobs.

---

## 🛠️ Practical Skills Gained
This lesson translates directly into tech and analytical skills used by professionals every day:

| Skill | Practical Example in this Project |
| :--- | :--- |
| **Data Cleaning & Management** | Understanding that raw files contain junk headers (WiGLE system metadata) that must be filtered out before analyzing. |
| **Geographic Information Systems (GIS)** | Mapping physical coordinates (Lat/Long) onto web tiles and understanding how map overlays (polygons, points, heatmaps) work. |
| **Troubleshooting Infrastructure** | Using real-world tools to measure physical properties (RF signal strength) and using data to diagnose a hardware bottleneck. |
| **Data Presentation / Reporting** | Explaining a technical problem (Wi-Fi coverage gap) to a non-technical audience (School Admins) using clear charts and map visuals. |

---

## 💼 Related Career Paths & Jobs
Explain to students that the skills they used in this lesson are highly valued in these careers:

### 1. 📶 Network Engineer / System Administrator
*   **What they do:** Design, build, and maintain a school's, hospital's, or corporation's network. They decide where to place Wi-Fi routers (Access Points) to ensure thousands of users can connect simultaneously.
*   **Connection to this Lesson:** They use specialized software (like NetSpot or Ekahau) to perform professional site surveys, checking signal dBm and channel overlap, just like this project.

### 2. 🗺️ GIS (Geographic Information Systems) Specialist
*   **What they do:** Build maps and analyze spatial data for city planning, environmental conservation, delivery routing (like FedEx/Amazon), or emergency response.
*   **Connection to this Lesson:** They overlay physical data (like traffic, pollution, or Wi-Fi signals) onto geographical maps to find spatial patterns.

### 3. 🛡️ Cybersecurity Analyst / Penetration Tester
*   **What they do:** Protect organizations from hackers.
*   **Connection to this Lesson:** A security analyst will perform "wardriving" or wireless auditing to look for **Rogue Access Points** (unauthorized routers plugged into the school network) or **Evil Twin** hotspots that try to trick students into connecting to steal their passwords.

### 4. 📊 Data Analyst / Data Scientist
*   **What they do:** Take huge, messy spreadsheets of data from many sources, clean them up, write code to analyze them, and build dashboard charts to help business leaders make smart decisions.
*   **Connection to this Lesson:** They aggregate files from 30 different students, average out coordinates into a grid, filter out empty rows, and build clear visualizations.
