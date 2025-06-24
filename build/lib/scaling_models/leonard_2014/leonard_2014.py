{
  "Leonard 2014": {
    "description": "Self-Consistent Earthquake Fault-Scaling Relations from Leonard (2014), BSSA.",
    "fault_types": {
      "Interplate Dip-Slip": {
        "A_from_L": [
          {
            "description": "Area from Length (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 2.0 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "m^2" },
            "range_x": [0, 5360]
          },
          {
            "description": "Area from Length (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 1.243, "b": 1.667 },
            "std_dev_a": "1.08 to 1.40",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [5360, null]
          }
        ],
        "W_from_L": [
          {
            "description": "Width from Length (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 1.0 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "m" },
            "range_x": [0, 5360]
          },
          {
            "description": "Width from Length (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 1.243, "b": 0.667 },
            "std_dev_a": "1.08 to 1.40",
            "units": { "x": "m", "y": "m" },
            "range_x": [5360, null]
          }
        ],
        "W_from_A": [
          {
            "description": "Width from Area (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 0.5 },
            "std_dev_a": null,
            "units": { "x": "m^2", "y": "m" },
            "range_x": [0, 28700000]
          },
          {
            "description": "Width from Area (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.746, "b": 0.4 },
            "std_dev_a": "0.65 to 0.84",
            "units": { "x": "m^2", "y": "m" },
            "range_x": [28700000, null]
          }
        ],
        "D_from_A": [
          {
            "description": "Average Displacement from Area",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": -4.420, "b": 0.5 },
            "std_dev_a": "-4.82 to -3.92",
            "units": { "x": "m^2", "y": "m" },
            "range_x": [0, null]
          }
        ],
        "D_from_L": [
          {
            "description": "Average Displacement from Length (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": -4.420, "b": 1.0 },
            "std_dev_a": "-4.90 to -3.82",
            "units": { "x": "m", "y": "m" },
            "range_x": [0, 5360]
          },
          {
            "description": "Average Displacement from Length (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": -3.799, "b": 0.833 },
            "std_dev_a": "-4.28 to -3.22",
            "units": { "x": "m", "y": "m" },
            "range_x": [5360, null]
          }
        ],
        "D_from_W": [
          {
            "description": "Average Displacement from Width",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": -5.352, "b": 1.25 },
            "std_dev_a": "-5.63 to -4.97",
            "units": { "x": "m", "y": "m" },
            "range_x": [5360, null]
          }
        ],
        "M0_from_A": [
          {
            "description": "Seismic Moment from Area",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 6.098, "b": 1.5 },
            "std_dev_a": "5.70 to 6.60",
            "units": { "x": "m^2", "y": "Nm" },
            "range_x": [0, null]
          }
        ],
        "M0_from_L": [
          {
            "description": "Seismic Moment from Length (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 6.098, "b": 3.0 },
            "std_dev_a": "5.45 to 6.83",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, 5360]
          },
          {
            "description": "Seismic Moment from Length (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 7.963, "b": 2.5 },
            "std_dev_a": "7.31 to 8.70",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [5360, null]
          }
        ],
        "M0_from_W": [
          {
            "description": "Seismic Moment from Width",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 3.301, "b": 3.75 },
            "std_dev_a": "3.27 to 3.45",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [5360, null]
          }
        ],
        "M0_from_D": [
          {
            "description": "Seismic Moment from Average Displacement",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 14.939, "b": 3.0 },
            "std_dev_a": "14.44 to 15.34",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, null]
          }
        ],
        "Mw_from_A": [
          {
            "description": "Moment Magnitude from Area",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.00, "b": 1.0 },
            "std_dev_a": "3.73-4.33",
            "units": { "x": "km^2", "y": null },
            "range_x": [0, null]
          }
        ],
        "Mw_from_L": [
          {
            "description": "Moment Magnitude from Length (self-similar growth)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.00, "b": 2.0 },
            "std_dev_a": null,
            "units": { "x": "km", "y": null },
            "range_x": [0, 5.36]
          },
          {
            "description": "Moment Magnitude from Length (fractal growth)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.24, "b": 1.667 },
            "std_dev_a": "3.81-4.73",
            "units": { "x": "km", "y": null },
            "range_x": [5.36, null]
          }
        ],
        "Mw_from_W": [
           {
            "description": "Moment Magnitude from Width",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 3.63, "b": 2.5 },
            "std_dev_a": "3.61-3.73",
            "units": { "x": "km", "y": null },
            "range_x": [5.4, null]
          }
        ],
        "Mw_from_D": [
           {
            "description": "Moment Magnitude from Average Displacement",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 6.84, "b": 2.0 },
            "std_dev_a": "6.17-7.38",
            "units": { "x": "m", "y": null },
            "range_x": [0, null]
          }
        ]
      },
      "Interplate Strike-Slip": {
        "A_from_L": [
          {
            "description": "Area from Length (self-similar)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 2.0 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "m^2" },
            "range_x": [0, 3400]
          },
          {
            "description": "Area from Length (fractal)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 1.176, "b": 1.667 },
            "std_dev_a": "1.04 to 1.30",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [3400, 40000]
          },
          {
            "description": "Area from Length (width-limited)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 4.244, "b": 1.0 },
            "std_dev_a": "4.11 to 4.37",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [40000, null]
          }
        ],
        "M0_from_L": [
           {
            "description": "Seismic Moment from Length (self-similar)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 6.087, "b": 3.0 },
            "std_dev_a": "5.49 to 6.66",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, 3400]
          },
          {
            "description": "Seismic Moment from Length (fractal)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 7.851, "b": 2.5 },
            "std_dev_a": "7.41 to 8.28",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [3400, 40000]
          },
          {
            "description": "Seismic Moment from Length (width-limited)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 12.45, "b": 1.5 },
            "std_dev_a": "11.86 to 13.03",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [40000, null]
          }
        ],
        "Mw_from_L": [
          {
            "description": "Moment Magnitude from Length (self-similar & fractal)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.17, "b": 1.667 },
            "std_dev_a": "3.77-4.55",
            "units": { "x": "km", "y": null },
            "range_x": [3.4, 45.0]
          },
          {
            "description": "Moment Magnitude from Length (width-limited)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 5.27, "b": 1.0 },
            "std_dev_a": null,
            "units": { "x": "km", "y": null },
            "range_x": [45.0, null]
          }
        ]
      },
      "SCR Dip-Slip": {
         "A_from_L": [
          {
            "description": "Area from Length (self-similar growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 2.0 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "m^2" },
            "range_x": [0, 2500]
          },
          {
            "description": "Area from Length (fractal growth)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 1.130, "b": 1.667 },
            "std_dev_a": "1.04 to 1.23",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [2500, null]
          }
        ],
        "M0_from_L": [
          {
            "description": "Seismic Moment from Length (self-similar)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 6.382, "b": 3.0 },
            "std_dev_a": "6.08 to 6.67",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, 2500]
          },
          {
            "description": "Seismic Moment from Length (fractal)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 8.077, "b": 2.5 },
            "std_dev_a": "7.78 to 8.36",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [2500, null]
          }
        ],
        "M0_from_L_SR": [
          {
            "description": "Seismic Moment from Surface Rupture Length (shallow)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 12.55, "b": 1.43 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, 15000]
          },
          {
            "description": "Seismic Moment from Surface Rupture Length (deep)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 8.08, "b": 2.5 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "Nm" },
            "range_x": [15000, null]
          }
        ],
        "Mw_from_L": [
          {
            "description": "Moment Magnitude from Length",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.32, "b": 1.667 },
            "std_dev_a": "4.12-4.51",
            "units": { "x": "km", "y": null },
            "range_x": [2.5, null]
          }
        ],
        "Mw_from_L_SR": [
          {
            "description": "Moment Magnitude from Surface Rupture Length (shallow)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 5.12, "b": 0.953 },
            "std_dev_a": null,
            "units": { "x": "km", "y": null },
            "range_x": [0, 15]
          },
          {
            "description": "Moment Magnitude from Surface Rupture Length (deep)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.32, "b": 1.667 },
            "std_dev_a": null,
            "units": { "x": "km", "y": null },
            "range_x": [15, null]
          }
        ]
      },
      "SCR Strike-Slip": {
        "A_from_L": [
          {
            "description": "Area from Length (self-similar)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 0.0, "b": 2.0 },
            "std_dev_a": null,
            "units": { "x": "m", "y": "m^2" },
            "range_x": [0, 1600]
          },
          {
            "description": "Area from Length (fractal)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 1.068, "b": 1.667 },
            "std_dev_a": "0.996 to 1.16",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [1600, 70000]
          },
          {
            "description": "Area from Length (width-limited)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 4.298, "b": 1.0 },
            "std_dev_a": "4.23 to 4.39",
            "units": { "x": "m", "y": "m^2" },
            "range_x": [70000, null]
          }
        ],
        "M0_from_L": [
           {
            "description": "Seismic Moment from Length (self-similar)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 6.370, "b": 3.0 },
            "std_dev_a": "6.10 to 6.65",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [0, 1600]
          },
          {
            "description": "Seismic Moment from Length (fractal)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 7.972, "b": 2.5 },
            "std_dev_a": "7.70 to 8.25",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [1600, 60000]
          },
          {
            "description": "Seismic Moment from Length (width-limited)",
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": { "a": 12.750, "b": 1.5 },
            "std_dev_a": "12.48 to 13.03",
            "units": { "x": "m", "y": "Nm" },
            "range_x": [60000, null]
          }
        ],
        "Mw_from_L": [
          {
            "description": "Moment Magnitude from Length (self-similar & fractal)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 4.25, "b": 1.667 },
            "std_dev_a": "4.07-4.43",
            "units": { "x": "km", "y": null },
            "range_x": [1.6, 70]
          },
          {
            "description": "Moment Magnitude from Length (width-limited)",
            "source": "Table 4",
            "equation_form": "Y = a + b * log10(X)",
            "coefficients": { "a": 5.44, "b": 1.0 },
            "std_dev_a": null,
            "units": { "x": "km", "y": null },
            "range_x": [60, null]
          }
        ]
      }
    }
  }
}
