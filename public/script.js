window.addEventListener("DOMContentLoaded", function () {
        // --- Initialize Socket.IO ---
        const socket = io();
        // throttle settings
        let lastControllerEmitTime = 0;
        const emitInterval = 1000 / 3; // ≈333 ms between sends
        // --- Handle sensor data from the server ---
        const sensorMapping = {
          temperaturapeacock: {
            element: document.getElementById("temperature-value"),
            format: (val) => val + "°C",
          },
          presionpeacock: {
            element: document.getElementById("pressure-value"),
            format: (val) => val + " hPa",
          },
          luzpeacock: {
            element: document.getElementById("light-value"),
            format: (val) => val + " lux",
          },
          humedadpeacock: {
            element: document.getElementById("humidity-value"),
            format: (val) => val + "%",
          },
          calidadairepeacock: {
            element: document.getElementById("airquality-value"),
            format: (val) => {
              const aqi = Number(val);
              let quality = "Good";
              if (aqi > 50) quality = "Moderate";
              if (aqi > 100) quality = "Unhealthy";
              return `${quality} (${aqi} AQI)`;
            },
          },
          poderpeacock: {
            element: document.getElementById("power-value"),
            format: (val) => val + "%",
          },
        };

        socket.on("sensorData", ({ topic, data }) => {
          console.log("socket → sensorData", topic, data);
          if (sensorMapping[topic]) {
            sensorMapping[topic].element.textContent =
              sensorMapping[topic].format(data);
          }
        });

        // --- Widget Toggle Functionality ---
        const widgetModes = ["side", "overlay", "off"];
        let widgetModeIndex = 0;
        const widget = document.querySelector(".widget");
        const content = document.querySelector(".content");
        const videoContainer = document.querySelector(".video-container");
        const toggleButton = document.getElementById("toggle-widget");

        function updateWidgetMode() {
          const mode = widgetModes[widgetModeIndex];
          if (mode === "side") {
            if (widget.parentNode !== content) {
              content.appendChild(widget);
            }
            widget.classList.remove("overlay");
            widget.style.display = "flex";
          } else if (mode === "overlay") {
            if (widget.parentNode !== videoContainer) {
              videoContainer.appendChild(widget);
            }
            widget.classList.add("overlay");
            widget.style.display = "flex";
          } else if (mode === "off") {
            widget.style.display = "none";
          }
          toggleButton.textContent = "Toggle Panel (" + mode + ")";
        }

        toggleButton.addEventListener("click", function () {
          widgetModeIndex = (widgetModeIndex + 1) % widgetModes.length;
          updateWidgetMode();
        });

        updateWidgetMode();

        // --- Gamepad Handling and Controller Data ---
        let gamepadState = {};

        function updateGamepad() {
          const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
          const gp = gamepads[0];
          if (gp) {
            gamepadState = {
              id: gp.id,
              index: gp.index,
              buttons: gp.buttons.map((button) => ({
                pressed: button.pressed,
                value: button.value,
              })),
              axes: gp.axes.slice(0),
            };

            let diagramHTML = `<h3>Controller Status</h3>`;
            diagramHTML += `<p><strong>ID:</strong> ${gamepadState.id}</p>`;
            diagramHTML += `<p><strong>Index:</strong> ${gamepadState.index}</p>`;
            diagramHTML += `<h4>Buttons</h4><ul>`;
            gp.buttons.forEach((button, index) => {
              diagramHTML += `<li>Button ${index}: ${button.value.toFixed(2)} ${
                button.pressed ? "(pressed)" : ""
              }</li>`;
            });
            diagramHTML += `</ul>`;
            diagramHTML += `<h4>Axes</h4><ul>`;
            gp.axes.forEach((axis, index) => {
              diagramHTML += `<li>Axis ${index}: ${axis.toFixed(2)}</li>`;
            });
            diagramHTML += `</ul>`;
            document.getElementById("controller-diagram").innerHTML =
              diagramHTML;

            // Extract and send joystick data [x1, y1, x2, y2] via Socket.IO
            // Extract and send joystick data [x1, y1, x2, y2] via Socket.IO,
            // rounding each value to two decimals.
            const joystickData = [
              Math.round((gp.axes[0] || 0) * 100) / 100,
              Math.round((gp.axes[1] || 0) * 100) / 100,
              Math.round((gp.axes[2] || 0) * 100) / 100,
              Math.round((gp.axes[3] || 0) * 100) / 100,
            ];
            const now = Date.now();
            if (now - lastControllerEmitTime >= emitInterval) {
              socket.emit("controllerData", joystickData);
              lastControllerEmitTime = now;
            }
          } else {
            document.getElementById(
              "controller-diagram"
            ).innerHTML = `<h3>Controller Status</h3><p>No controller detected.</p>`;
          }
          requestAnimationFrame(updateGamepad);
        }

        requestAnimationFrame(updateGamepad);
        const streamImg = document.getElementById("server-stream");

        async function onProcessClick() {
       const res = await fetch('/screenshot');
       const { response, error } = await res.json();
       if (error) {
        console.error(error);
          return;
            }
           speak(response);
          }

// wire up your button
document.getElementById('screenshot-btn')
  .addEventListener('click', onProcessClick);

        function speak(text) {
          // stop any current speech
          window.speechSynthesis.cancel();
          // build the utterance
          const utter = new SpeechSynthesisUtterance(text);
          utter.rate = 1; // playback speed (0.1–10)
          utter.pitch = 1; // pitch (0–2)
          // you can pick a voice here:
          // utter.voice = speechSynthesis.getVoices().find(v => v.name === 'Google UK English Male');
          window.speechSynthesis.speak(utter);
        }

        fetch("/screenshot")
          .then((res) => res.json())
          .then(({ response, error }) => {
            if (error) return alert(error);
            speak(response);
          });

        socket.on("sensorData", ({ topic, data }) => {
          const cfg = THRESHOLDS[topic];
          const el = sensorMapping[topic].element;
          el.textContent = sensorMapping[topic].format(data);

          // reset
          el.classList.remove("value-increasing", "value-decreasing");

          if (cfg) {
            if (data > cfg.high) el.classList.add("value-increasing");
            if (data < cfg.low) el.classList.add("value-decreasing");
          }
        });
      });
      const streamImg = document.getElementById("server-stream");
      let showingRaw = true;

      const THRESHOLDS = {
        temperaturapeacock: { low: 20, high: 30 },
        humedadpeacock: { low: 30, high: 60 },
        luzpeacock: { low: 300, high: 1000 },
        presionpeacock: { low: 850, high: 1100 },
        calidadairepeacock: { low: 0, high: 100 },
        poderpeacock: { low: 20, high: 100 },
      };

      document.addEventListener('DOMContentLoaded', function() {
        // Panel toggle functionality
        const panel = document.getElementById('side-panel');
        const panelToggle = document.getElementById('panel-toggle');
        const closePanel = document.getElementById('close-panel');
        const overlay = document.getElementById('panel-overlay');
        
        // Open panel
        panelToggle.addEventListener('click', function() {
          panel.classList.add('open');
          overlay.classList.add('active');
        });
        
        // Close panel
        function closeThePanel() {
          panel.classList.remove('open');
          overlay.classList.remove('active');
        }
        
        closePanel.addEventListener('click', closeThePanel);
        overlay.addEventListener('click', closeThePanel);
        
        // Connect panel buttons to existing functionality
        const toggleWidgetBtn = document.getElementById('toggle-widget');
        const toggleWidgetPanelBtn = document.getElementById('toggle-widget-panel');
        
        toggleWidgetPanelBtn.addEventListener('click', function() {
          toggleWidgetBtn.click();
          closeThePanel();
        });
        
        const screenshotBtn = document.getElementById('screenshot-btn');
        const screenshotPanelBtn = document.getElementById('screenshot-btn-panel');
        
        screenshotPanelBtn.addEventListener('click', function() {
          screenshotBtn.click();
          closeThePanel();
        });
        
        const viewLogsBtn = document.getElementById('view-logs-panel');
        viewLogsBtn.addEventListener('click', function() {
          window.open('/anomalies/pdf','_blank');
          closeThePanel();
        });
        
        // Add functionality for other buttons
        // For demonstration purposes, these just show alerts
        const newButtons = [
          'start-robot', 'stop-robot', 'reset-position',
          'camera-settings', 'zoom-in', 'zoom-out',
          'weather-forecast', 'terrain-analysis'
        ];
        
        newButtons.forEach(btnId => {
          const btn = document.getElementById(btnId);
          if (btn) {
            btn.addEventListener('click', function() {
              // Replace this with actual functionality
              alert(`Button pressed: ${btnId}`);
              closeThePanel();
            });
          }
        });
      });