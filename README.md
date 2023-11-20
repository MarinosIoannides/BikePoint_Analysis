# BikePoint Analysis

This project aims to answer the following:
- Where London’s BikePoints are currently?
- How do areas with BikePoints differ from areas without?
- Where might benefit from new BikePoints from a public health perspective?

# Installing and Running the project

First, clone the repository.

Then run:

    python run_model.py

from within the "BikePoint_Analysis" directory. 

This will open an interactive Dash Dashboard in your browser.

# Updating Data

The project contains raw and preprocessed data, which is all open access.

Some of the data is updated through APIs. This can be done by running

    python get_data.py
    python clean_data.py

from within the "BikePoint_Analalysis" directory.

These will download new data from APIs and then clean / process the data for the model to run.

# Dependencies

The following packages are required to run the product.

- folium
- polars
- pandas 
- dash 
- plotly.express
- threading
- statsmodels.api 
- webbrowser
- requests

