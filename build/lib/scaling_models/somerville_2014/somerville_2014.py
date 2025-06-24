{
  "Somerville 2014": {
    "description": "Scaling relations between seismic moment and rupture area of earthquakes in stable continental regions from Somerville (2014), PEER Report 2014/14.",
    "fault_types": {
      "SCR - Aftershock Method": {
        "A_from_M0": [
          {
            "source": "Table 3",
            "equation_form": "log10(Y) = a * log10(X) + b",
            "coefficients": {
              "a": 0.66667,
              "b": -14.876
            },
            "units": {
              "x": "dyne.cm",
              "y": "km^2"
            },
            "range_x": [
              null,
              null
            ]
          }
        ]
      },
      "SCR - Duration Method": {
        "A_from_M0": [
          {
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": {
              "a": 0.66667,
              "b": -15.028
            },
            "units": {
              "x": "dyne.cm",
              "y": "km^2"
            },
            "range_x": [
              null,
              null
            ]
          }
        ]
      },
      "SCR - Slip Model Method": {
        "A_from_M0": [
          {
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": {
              "a": 0.66667,
              "b": -14.934
            },
            "units": {
              "x": "dyne.cm",
              "y": "km^2"
            },
            "range_x": [
              null,
              null
            ]
          }
        ]
      },
      "SCR - Combined Methods": {
        "A_from_M0": [
          {
            "source": "Table 3",
            "equation_form": "log10(Y) = a + b * log10(X)",
            "coefficients": {
              "a": 0.66667,
              "b": -14.946
            },
            "units": {
              "x": "dyne.cm",
              "y": "km^2"
            },
            "range_x": [
              null,
              null
            ]
          }
        ]
      }
    }
  }
}
