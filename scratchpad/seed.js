// Dev-only: seed localStorage with a small program that covers every RPE case.
(function () {
  var s = {
    version: 1, people: ["Daniel"], weights: {}, goals: {}, bodyweights: [],
    logs: [], activePerson: 0, theme: "light",
    program: {
      order: ["t"],
      sessions: {
        t: {
          name: "Test day", day: "Wednesday", exercises: [
            { name: "Squat", target: "3 x 5", sets: 3, cols: ["Weight (kg)", "Reps"] },
            { name: "Walking/sandbag lunges", target: "3 x 20 m", sets: 3, cols: ["Weight (kg)", "Distance (m)"] },
            { name: "Warm-up jog", target: "5 min", sets: 1, cols: ["Min", "Notes"] },
            { name: "Treadmill intervals", target: "6 x 1 min", sets: 6, cols: ["Hard speed (km/h)", "Easy speed (km/h)"], garminRun: true },
            { name: "Easy run (Zone 2)", target: "5 km", sets: 1, cols: ["Distance (km)", "Time (mm:ss)", "Pace"] }
          ]
        }
      }
    }
  };
  localStorage.setItem("flLiveTracker_v1", JSON.stringify(s));
  window.__seeded = true;
})();
