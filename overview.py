"""Automatic generation of overview files for measurement data."""
import csv
import os
from typing import List, Optional
import warnings


class Overview:
    """Manages a CSV overview file for a specific measurement.

    If an appropriate overview file already exists in the target directory,
    new measurements will be appended. If not, a new overview file will be
    created.

    The file name is generated automatically according to the following scheme:
    "overview_MEASUREMENTNAME.dat"
    where "MEASUREMENTNAME" is the name of the measurement method class.

    Attributes:
        _target_directory
        _measurement_name
        _column_names
        _comment_lines
    """

    COMMENT_CHAR = "#"  # The character signalling the beginning of a CSV comment
    CSV_SEPARATOR = " "
    
    def __init__(self, target_directory: str,
                 measurement_name: str, column_names: List[str],
                 comment_lines: List[str] = []) -> None:
        """
        :param target_directory: Directory in which to create/append to an overview file
        :param measurement_name: Name of the measurement class
        :param column_names: Names of CSV columns in the overview file
        :param comment_lines: Lines to write to the top of the overview file as comments
        """
        self._target_directory = target_directory
        self._measurement_name = measurement_name
        self._column_names = column_names
        self._comment_lines = comment_lines

        existing_file = self._find_existing()
        if existing_file is None:
            self._create_new()
    

    def add_measurement(self, **data) -> None:
        """Add a row to the overview file which contains the values of 'data'.

        :param data: Keys are column names, values are corresponding data.
                     All column names of this overview must be in the keys.

        """
        if (set(self._column_names) - data.keys()) != set():
            raise RuntimeError(
                "Not all columns of the overview were filled with values.\n"
                "Expected columns: {}\nReceived columns: {}".format(self._column_names,
                                                                    list(data.keys))
            )
        for key in data.keys():
            if key not in self._column_names:
                warnings.warn(
                    "Unexpected column {} will not be appended to the overview file.".format(key)
                )
                data.pop(key)

        with open(self._file_path, "a") as outfile:
            # Filter out lines that are comments:
            writer = csv.DictWriter(outfile, self._column_names,
                                    delimiter=self.CSV_SEPARATOR)
            writer.writerow(data)

    @property
    def _file_path(self) -> str:
        file_name = "overview_{}.dat".format(self._measurement_name)
        full_path = os.path.join(self._target_directory, file_name)
        return full_path

    def _find_existing(self) -> Optional[str]:
        """Returns the path of an existing overview file or 'None' if none exists."""
        
        if os.path.isfile(self._file_path):
            return self._file_path
        else:
            return None

    def _create_new(self) -> None:
        """Create a new overview file and write its header."""

        with open(self._file_path, "w") as outfile:
            for comment in self._comment_lines:
                outfile.write("{} {}\n".format(self.COMMENT_CHAR, comment))

            writer = csv.DictWriter(outfile, fieldnames=self._column_names, delimiter=self.CSV_SEPARATOR)
            writer.writeheader()

            
if __name__ == "__main__":
    from datetime import datetime
    
    measurement_class_name = "MyTestMethod"
    columns = ["Datetime", "Resistance", "Temperature"]
    comment_lines = ["This is a test overview file", "Nothing to see here"]

    overview = Overview("/tmp", measurement_class_name, columns, comment_lines)
    overview.add_measurement(Datetime=datetime.now().isoformat(), Resistance=1.23,
                             Temperature=1.234)

    
