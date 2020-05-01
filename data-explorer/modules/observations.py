import os

import hvplot.pandas  # noqa
import pandas as pd  # noqa
import panel as pn
import param
import pendulum
from astropy.coordinates import SkyCoord
from bokeh.models import (ColumnDataSource, DataTable, DateFormatter,
                          NumberFormatter, TableColumn)
from panoptes.utils.data import search_observations

pn.extension()

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')


class ObservationsExplorer(param.Parameterized):
    """Param interface for inspecting observations"""
    collection = param.String(
        doc='Firestore collection',
        default='observations',
        readonly=True,
        precedence=-1  # Don't show widget
    )

    df = param.DataFrame(
        doc='The DataFrame for the observations.',
        precedence=-1  # Don't show widget
    )

    search_name = param.String(
        label='Coordinates for object',
        doc='Field name for coordinate lookup',
    )
    coords = param.XYCoordinates(
        label='RA/Dec Coords [deg]',
        doc='RA/Dec Coords [degrees]', default=(0, 0)
    )
    radius = param.Number(
        label='Search radius [degrees]',
        doc='Search radius [degrees]',
        default=5.0,
        bounds=(0, 180),
        softbounds=(1, 15)
    )
    time = param.DateRange(
        label='Date Range',
        default=(pendulum.parse('2018-01-01'), pendulum.now()),
        bounds=(pendulum.parse('2018-01-01'), pendulum.now())
    )
    min_num_images = param.Integer(
        doc='Minimum number of images.',
        default=1,
        bounds=(1, 50),
        softbounds=(1, 10)
    )
    unit_id = param.ListSelector(
        doc='Unit IDs',
        label='Unit IDs',
    )
    search_button = pn.widgets.Button(
        name='Search observations!',
        button_type='success',
        sizing_mode='scale_width'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        # Set some default for the params now that we have data.
        # TODO(wtgee) look up unit ids (once).
        units = [
            'The Whole World! 🌎',
            'PAN001',
            'PAN006',
            'PAN008',
            'PAN012',
            'PAN018',
        ]
        self.param.unit_id.objects = units
        self.unit_id = [units[0]]

        def do_search(event):
            event.obj.name = 'Searching...'
            event.obj.button_type = 'warning'

            self.update_data()

            event.obj.name = 'Search observations!'
            event.obj.button_type = 'success'

        self.search_button.on_click(do_search)

        # Get recent results
        self.df = search_observations(ra=0,
                                      dec=0,
                                      radius=180,
                                      start_date=pendulum.now().subtract(weeks=2),
                                      end_date=pendulum.now(),
                                      min_num_images=1,
                                      )

    def update_data(self):
        # If using the default unit_ids option, then search for all.
        unit_ids = self.unit_id
        if unit_ids == self.param.unit_id.objects[0:1]:
            unit_ids = self.param.unit_id.objects[1:]

        if self.search_name != '':
            coords = SkyCoord.from_name(self.search_name)
            self.coords = (
                round(coords.ra.value, 3),
                round(coords.dec.value, 3)
            )

        self.df = search_observations(ra=self.coords[0],
                                      dec=self.coords[1],
                                      radius=self.radius,
                                      start_date=self.time[0],
                                      end_date=self.time[1],
                                      min_num_images=self.min_num_images,
                                      unit_ids=unit_ids
                                      )

    @property
    @param.depends('df')
    def source(self):
        return ColumnDataSource(data=self.df)

    def widget_box(self):
        return pn.WidgetBox(
            pn.Param(
                self.param,
                widgets={
                    'unit_id': pn.widgets.MultiChoice,
                    'search_name': {
                        "type": pn.widgets.TextInput,
                        "placeholder": "Lookup RA/Dec by object name"
                    },
                }
            ),
            self.search_button,
            sizing_mode='scale_width',
            width=300
        )

    @param.depends('df')
    def plot(self):
        selected = self.source.selected.indices
        if len(selected) == 0:
            df = self.df
        else:
            df = self.df.iloc[self.source.selected.indices]

        field_summary_df = df.groupby('field_name').sum().reset_index()
        print(field_summary_df)

        bar_plot = field_summary_df.hvplot.bar(
            x='field_name',
            y='total_minutes_exptime',
            rot=45,
            tools=['box_select', 'lasso_select', 'hover', 'help']
        ).opts(
            title='Total Exptime',
            width=300,
            xlabel='Field Name',
            ylabel='Total Exptime [min]',
        )

        return bar_plot

    @param.depends('df')
    def table(self):
        columns = [
            TableColumn(field="unit_id", title="Unit ID", width=100),
            TableColumn(field="sequence_id", title="Sequence ID", width=500),
            TableColumn(field="field_name", title="Field Name", width=350),
            TableColumn(field="ra", title="RA", formatter=NumberFormatter(format="0.000"), width=100),
            TableColumn(field="dec", title="dec", formatter=NumberFormatter(format="0.000"), width=100),
            TableColumn(field="time", title="time", formatter=DateFormatter(format='%Y-%m-%d %H:%M'), width=200),
            TableColumn(field="num_images", title="Images", width=75),
            TableColumn(field="exptime", title="Exptime [sec]", formatter=NumberFormatter(format="0.00"), width=150),
            TableColumn(field="total_minutes_exptime", title="Total Minutes", formatter=NumberFormatter(format="0.0"),
                        width=150),
        ]

        data_table = DataTable(
            source=self.source,
            columns=columns,
            width=1000,
        )

        def row_selected(attrname, old, new):
            print(attrname, old, new)

        self.source.selected.on_change('indices', row_selected)

        return data_table