"""Background transfer jobs monitoring table and controls.

Complies with NASA JPL Power of 10 rules.
"""

from typing import Dict, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from osb.core.models import JobStatus, TransferJob
from osb.core.transfer_mgr import TransferManager
from osb.core.utils import format_bytes
from osb.gui.outline_icons import OutlineIcons


class JobLogDialog(QDialog):
    """View streaming execution logs of a transfer job."""

    def __init__(self, job: TransferJob, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        assert job is not None, "Job cannot be None"
        self._job = job
        self.setWindowTitle(f"Job Telemetry - {job.job_id}")
        self.resize(600, 360)
        self.setWindowIcon(OutlineIcons.get_icon("info"))

        layout = QVBoxLayout(self)
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setStyleSheet("background-color: #111215; font-family: monospace; font-size: 11px;")

        logs_content = "\n".join(job.log_lines) if job.log_lines else "No detailed log entries."
        if job.error_message:
            logs_content += f"\n\nERROR:\n{job.error_message}"
        self._text.setPlainText(logs_content)

        layout.addWidget(self._text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class JobsView(QWidget):
    """Bottom panel displaying real-time background jobs."""

    def __init__(self, transfer_mgr: TransferManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        assert transfer_mgr is not None, "TransferManager required"
        self._mgr = transfer_mgr
        self._row_map: Dict[str, int] = {}
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize the jobs monitoring panel layout."""
        assert self._mgr is not None, "Manager cannot be None"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        layout.addLayout(self._create_header_layout())
        self._table = self._create_jobs_table()
        layout.addWidget(self._table)
        assert self._table is not None, "Table must be created"

    def _create_header_layout(self) -> QHBoxLayout:
        """Create header toolbar with title, toggle, and clear buttons."""
        header_layout = QHBoxLayout()
        title = QLabel("BACKGROUND TRANSFER JOBS")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #9ca3af; letter-spacing: 0.5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._is_collapsed = False
        self._toggle_btn = QPushButton("Collapse")
        self._toggle_btn.setIcon(OutlineIcons.get_icon("minus"))
        self._toggle_btn.setToolTip("Minimize / Collapse transfer jobs view")
        self._toggle_btn.clicked.connect(self.toggle_collapsed)
        header_layout.addWidget(self._toggle_btn)

        clear_btn = QPushButton("Clear Completed")
        clear_btn.setIcon(OutlineIcons.get_icon("trash"))
        clear_btn.clicked.connect(self._clear_completed)
        header_layout.addWidget(clear_btn)
        return header_layout

    def _create_jobs_table(self) -> QTableWidget:
        """Construct the jobs table widget."""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "ID", "Type", "Source", "Destination", "Current File", "Progress", "Speed", "ETA", "Status"
        ])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(2, 160)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(3, 160)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(5, 130)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.doubleClicked.connect(self._on_row_double_click)
        return table

    def toggle_collapsed(self) -> None:
        """Toggle table visibility between collapsed and expanded states."""
        assert self._table is not None, "Table must be initialized"
        self._is_collapsed = not self._is_collapsed
        self._table.setVisible(not self._is_collapsed)
        icon_name = "plus" if self._is_collapsed else "minus"
        btn_text = "Expand" if self._is_collapsed else "Collapse"
        self._toggle_btn.setIcon(OutlineIcons.get_icon(icon_name))
        self._toggle_btn.setText(btn_text)
        assert self._toggle_btn is not None, "Toggle button required"

    def _connect_signals(self) -> None:
        """Bind transfer manager signals to UI slots."""
        assert self._mgr is not None, "Manager must be present"
        self._mgr.job_added.connect(self._on_job_added)
        self._mgr.job_updated.connect(self._on_job_updated)
        self._mgr.job_finished.connect(self._on_job_finished)

    def _on_job_added(self, job: TransferJob) -> None:
        """Insert row for new background job."""
        assert isinstance(job, TransferJob), "Must be TransferJob"
        assert self._table is not None, "Table must exist"
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._row_map[job.job_id] = row

        self._table.setItem(row, 0, QTableWidgetItem(job.job_id))
        self._table.setItem(row, 1, QTableWidgetItem(job.op.value.upper()))
        src_label = f"{job.src_remote}:{job.src_path}" if job.src_remote else job.src_path
        dst_label = f"{job.dst_remote}:{job.dst_path}" if job.dst_remote else job.dst_path
        self._table.setItem(row, 2, QTableWidgetItem(src_label))
        self._table.setItem(row, 3, QTableWidgetItem(dst_label))
        self._table.setItem(row, 4, QTableWidgetItem(job.current_file or "--"))

        pbar = QProgressBar()
        pbar.setRange(0, 100)
        pbar.setValue(int(job.percentage))
        self._table.setCellWidget(row, 5, pbar)

        self._table.setItem(row, 6, QTableWidgetItem(job.speed_str))
        self._table.setItem(row, 7, QTableWidgetItem(job.eta_str))
        self._table.setItem(row, 8, QTableWidgetItem(job.status.value.upper()))

    def _on_job_updated(self, job_id: str) -> None:
        """Update metrics for an existing job row."""
        assert isinstance(job_id, str), "Job ID must be string"
        assert self._table is not None, "Table must exist"
        if job_id not in self._row_map:
            return
        row = self._row_map[job_id]
        job = self._mgr.get_job(job_id)
        if not job:
            return

        file_item = self._table.item(row, 4)
        file_val = job.current_file if job.current_file else ("Completed" if job.status == JobStatus.COMPLETED else "--")
        if file_item:
            file_item.setText(file_val)
        else:
            self._table.setItem(row, 4, QTableWidgetItem(file_val))

        pbar = self._table.cellWidget(row, 5)
        if isinstance(pbar, QProgressBar):
            pbar.setValue(int(job.percentage))

        self._table.setItem(row, 6, QTableWidgetItem(job.speed_str))
        self._table.setItem(row, 7, QTableWidgetItem(job.eta_str))
        self._table.setItem(row, 8, QTableWidgetItem(job.status.value.upper()))

    def _on_job_finished(self, job_id: str, success: bool, msg: str) -> None:
        """Update finished state and icon in status column."""
        assert isinstance(job_id, str), "Job ID must be string"
        self._on_job_updated(job_id)

    def _on_row_double_click(self) -> None:
        """Open log dialog for selected job."""
        row = self._table.currentRow()
        if row < 0:
            return
        job_id_item = self._table.item(row, 0)
        if not job_id_item:
            return
        job = self._mgr.get_job(job_id_item.text())
        if job:
            dlg = JobLogDialog(job, parent=self)
            dlg.exec()

    def _clear_completed(self) -> None:
        """Remove completed or failed jobs from table."""
        rows_to_remove = []
        for job_id, row in list(self._row_map.items()):
            job = self._mgr.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                rows_to_remove.append((row, job_id))

        rows_to_remove.sort(key=lambda x: x[0], reverse=True)
        for row, job_id in rows_to_remove:
            self._table.removeRow(row)

        self._row_map.clear()
        for r in range(self._table.rowCount()):
            item = self._table.item(r, 0)
            if item:
                self._row_map[item.text()] = r
