#  PyMODA, a Python implementation of MODA (Multiscale Oscillatory Dynamics Analysis).
#  Copyright (C) 2019  Lancaster University
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <https://www.gnu.org/licenses/>.
from typing import Optional

from PyQt5 import QtGui
from PyQt5.QtGui import QWindow

from data import resources
from gui.components.FreqComponent import FreqComponent
from gui.components.PreprocessComponent import PreprocessComponent
from gui.components.SingleSignalComponent import SingleSignalComponent
from gui.windows.common.BaseTFWindow import BaseTFWindow
from gui.windows.timefrequency.TFPresenter import TFPresenter
from gui.windows.timefrequency.TFViewProperties import TFViewProperties
from utils.decorators import floaty, deprecated


class TFWindow(TFViewProperties,
               PreprocessComponent,
               BaseTFWindow,
               FreqComponent,
               SingleSignalComponent):
    """
    The time-frequency window. This class is the "View" in MVP,
    meaning that it should defer responsibility for tasks to the
    presenter.
    """
    name = "Time-Frequency Analysis"

    # The items to be shown in the "WT / WFT Type" combobox.
    window_items = (
        ["Gaussian", "Hann", "Blackman", "Exp", "Rect", "Kaiser-a"],  # Windowed Fourier transform.
        ["Lognorm", "Morlet", "Bump"],  # Wavelet transform.
    )

    def __init__(self, application, presenter=None):
        TFViewProperties.__init__(self)
        BaseTFWindow.__init__(self, application, presenter or TFPresenter(self))

        FreqComponent.__init__(self, self.line_fmax, self.line_fmin, self.line_res)
        SingleSignalComponent.__init__(self, self.signal_plot())
        PreprocessComponent.__init__(self, self.plot_preproc)

        self.presenter.init()

    def setup_ui(self):
        super().setup_ui()
        self.setup_radio_plot()
        self.setup_radio_transform()
        self.setup_combo_wt()

        amp = self.amplitude_plot()
        amp.set_xlabel("Average Amplitude")

    def on_calculate_started(self):
        super(TFWindow, self).on_calculate_started()
        self.amplitude_plot().clear()
        self.amplitude_plot().set_in_progress(True)

    def on_calculate_stopped(self):
        super(TFWindow, self).on_calculate_stopped()
        self.amplitude_plot().set_in_progress(False)

    def get_layout_file(self) -> str:
        return resources.get("layout:window_time_freq.ui")

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        """Called when the window closes. Cancels any calculations that are in progress."""
        self.presenter.on_close()
        super().closeEvent(e)

    def on_transform_toggled(self, is_wt):
        """Called when the type of transform (WT or WFT) is toggled."""
        self.setup_combo_wt(is_wt)

    def setup_combo_wt(self, is_wt=True):
        """
        Sets up the "WT / WFT Type" combobox according to the current transform type.
        :param is_wt: whether the current transform is WT (not WFT)
        """
        combo = self.combo_window
        combo.clear()

        # Gets the list of items from the tuple, since the bool evaluates to 0 or 1.
        items = self.window_items[is_wt]
        for i in items:
            combo.addItem(i)

    def setup_radio_plot(self):
        self.radio_plot_ampl.setChecked(True)
        self.radio_plot_ampl.toggled.connect(self.on_plot_type_toggled)

    def setup_radio_transform(self):
        self.radio_transform_wt.setChecked(True)
        self.radio_transform_wt.toggled.connect(self.on_transform_toggled)

    @floaty
    def get_fstep(self) -> Optional[float]:
        return None  # Placeholder.

    def get_padding(self) -> str:  # TODO: is this actually used in the algorithm?
        return None

    @floaty
    def get_rel_tolerance(self) -> Optional[float]:
        return None

    def get_wt_wft_type(self) -> str:
        combo = self.combo_window
        return combo.currentText()

    def get_transform_type(self) -> str:
        if self.radio_transform_wft.isChecked():
            transform = "wft"
        else:
            transform = "wt"
        return transform

    def setup_radio_cut_edges(self):
        self.radio_cut_on.setChecked(True)
