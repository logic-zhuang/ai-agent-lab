import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QListWidget, QListWidgetItem,
    QFileDialog, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QCheckBox, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QBrush
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import traceback


class LinearRegressionTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.numeric_columns = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SPSS线性回归分析工具")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        import_btn = QPushButton("导入数据文件")
        import_btn.setFont(QFont("微软雅黑", 11))
        import_btn.setMinimumHeight(40)
        import_btn.clicked.connect(self.import_data)
        left_layout.addWidget(import_btn)
        
        data_info_label = QLabel("数据信息：")
        data_info_label.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
        left_layout.addWidget(data_info_label)
        
        self.data_info = QTextEdit()
        self.data_info.setReadOnly(True)
        self.data_info.setMaximumHeight(150)
        self.data_info.setFont(QFont("微软雅黑", 9))
        left_layout.addWidget(self.data_info)
        
        y_label = QLabel("因变量 (Y):")
        y_label.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
        left_layout.addWidget(y_label)
        
        self.y_combo = QComboBox()
        self.y_combo.setFont(QFont("微软雅黑", 10))
        self.y_combo.setMinimumHeight(35)
        left_layout.addWidget(self.y_combo)
        
        x_label = QLabel("自变量 (X):")
        x_label.setFont(QFont("微软雅黑", 10, QFont.Weight.Bold))
        left_layout.addWidget(x_label)
        
        self.x_list = QListWidget()
        self.x_list.setFont(QFont("微软雅黑", 10))
        self.x_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.x_list.setMinimumHeight(150)
        left_layout.addWidget(self.x_list)
        
        analyze_btn = QPushButton("执行线性回归分析")
        analyze_btn.setFont(QFont("微软雅黑", 11, QFont.Weight.Bold))
        analyze_btn.setMinimumHeight(50)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        analyze_btn.clicked.connect(self.analyze)
        left_layout.addWidget(analyze_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.setFont(QFont("微软雅黑", 10))
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset)
        left_layout.addWidget(reset_btn)
        
        left_layout.addStretch()
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(300)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("微软雅黑", 10))
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier New", 9))
        self.tab_widget.addTab(self.output_text, "分析结果")
        
        self.model_summary_table = QTableWidget()
        self.model_summary_table.setFont(QFont("微软雅黑", 9))
        self.tab_widget.addTab(self.model_summary_table, "模型汇总表")
        
        self.coeff_table = QTableWidget()
        self.coeff_table.setFont(QFont("微软雅黑", 9))
        self.tab_widget.addTab(self.coeff_table, "系数表")
        
        self.anova_table = QTableWidget()
        self.anova_table.setFont(QFont("微软雅黑", 9))
        self.tab_widget.addTab(self.anova_table, "方差分析表")
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.tab_widget, 1)
        
        central_widget.setLayout(main_layout)

    def import_data(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "CSV files (*.csv);;Excel files (*.xlsx *.xls)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.df = pd.read_csv(file_path)
                else:
                    self.df = pd.read_excel(file_path)
                
                self.numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
                
                self.y_combo.clear()
                self.y_combo.addItems(self.numeric_columns)
                
                self.x_list.clear()
                for col in self.numeric_columns:
                    item = QListWidgetItem(col)
                    self.x_list.addItem(item)
                
                info_text = f"""
数据文件：{os.path.basename(file_path)}
总行数：{len(self.df)}
总列数：{len(self.df.columns)}

列名：
{', '.join(self.df.columns.tolist())}

数值列：
{', '.join(self.numeric_columns)}
                """
                self.data_info.setText(info_text)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入文件失败：{str(e)}")

    def analyze(self):
        if self.df is None:
            QMessageBox.warning(self, "警告", "请先导入数据文件")
            return
        
        y_var = self.y_combo.currentText()
        selected_x_items = self.x_list.selectedItems()
        
        if not y_var:
            QMessageBox.warning(self, "警告", "请选择因变量")
            return
        
        if not selected_x_items:
            QMessageBox.warning(self, "警告", "请选择至少一个自变量")
            return
        
        x_vars = [item.text() for item in selected_x_items]
        
        try:
            formula = f"{y_var} ~ {' + '.join(x_vars)}"
            
            model = ols(formula, data=self.df).fit()
            
            output = self.format_results(model, y_var, x_vars)
            self.output_text.setText(output)
            
            self.display_model_summary(model)
            self.display_coefficients(model)
            self.display_anova(model, self.df, formula)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败：{str(e)}\n{traceback.format_exc()}")

    def format_results(self, model, y_var, x_vars):
        output = """
═══════════════════════════════════════════════════════════════════════════════
                         SPSS线性回归分析结果
═══════════════════════════════════════════════════════════════════════════════

【模型信息】
"""
        output += f"因变量 (Y): {y_var}\n"
        output += f"自变量 (X): {', '.join(x_vars)}\n"
        output += f"样本量: {len(self.df)}\n"
        
        output += f"""
【模型汇总】
R平方 (R²)                    : {model.rsquared:.6f}
调整R平方 (Adjusted R²)       : {model.rsquared_adj:.6f}
标准误差 (Std. Error)         : {np.sqrt(model.mse_resid):.6f}
F统计量                      : {model.fvalue:.6f}
P值 (Sig.)                   : {model.f_pvalue:.6f}

【回归系数表】
"""
        
        for idx, (var, coef) in enumerate(model.params.items()):
            se = model.bse[var]
            t_stat = model.tvalues[var]
            p_val = model.pvalues[var]
            
            sig_marker = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
            
            output += f"""
变量: {var}
  系数 (B)           : {coef:15.6f}
  标准误差 (Std. Error): {se:15.6f}
  t统计量           : {t_stat:15.6f}
  P值 (Sig.)        : {p_val:15.6f} {sig_marker}
  置信区间 [95%]    : [{model.conf_int().loc[var, 0]:.6f}, {model.conf_int().loc[var, 1]:.6f}]
"""
        
        output += """
注：*** p<0.001, ** p<0.01, * p<0.05

【诊断信息】
"""
        output += f"对数似然值: {model.llf:.4f}\n"
        output += f"赤池信息准则 (AIC): {model.aic:.4f}\n"
        output += f"贝叶斯信息准则 (BIC): {model.bic:.4f}\n"
        output += f"剩余自由度: {model.df_resid}\n"
        
        output += "\n═══════════════════════════════════════════════════════════════════════════════\n"
        
        return output

    def display_model_summary(self, model):
        self.model_summary_table.setRowCount(6)
        self.model_summary_table.setColumnCount(2)
        self.model_summary_table.setHorizontalHeaderLabels(["指标", "数值"])
        
        rows = [
            ("R 平方 (R²)", f"{model.rsquared:.6f}"),
            ("调整 R 平方", f"{model.rsquared_adj:.6f}"),
            ("标准误差", f"{np.sqrt(model.mse_resid):.6f}"),
            ("F 统计量", f"{model.fvalue:.6f}"),
            ("P 值 (Sig.)", f"{model.f_pvalue:.6f}"),
            ("样本量", f"{len(self.df)}")
        ]
        
        for i, (label, value) in enumerate(rows):
            self.model_summary_table.setItem(i, 0, QTableWidgetItem(label))
            self.model_summary_table.setItem(i, 1, QTableWidgetItem(value))
        
        self.model_summary_table.resizeColumnsToContents()

    def display_coefficients(self, model):
        self.coeff_table.setRowCount(len(model.params))
        self.coeff_table.setColumnCount(7)
        self.coeff_table.setHorizontalHeaderLabels([
            "变量", "系数 (B)", "标准误差", "t 值", "P 值", "置信下界", "置信上界"
        ])
        
        conf_int = model.conf_int()
        
        for i, (var, coef) in enumerate(model.params.items()):
            se = model.bse[var]
            t_stat = model.tvalues[var]
            p_val = model.pvalues[var]
            ci_lower = conf_int.loc[var, 0]
            ci_upper = conf_int.loc[var, 1]
            
            self.coeff_table.setItem(i, 0, QTableWidgetItem(var))
            self.coeff_table.setItem(i, 1, QTableWidgetItem(f"{coef:.6f}"))
            self.coeff_table.setItem(i, 2, QTableWidgetItem(f"{se:.6f}"))
            self.coeff_table.setItem(i, 3, QTableWidgetItem(f"{t_stat:.6f}"))
            self.coeff_table.setItem(i, 4, QTableWidgetItem(f"{p_val:.6f}"))
            self.coeff_table.setItem(i, 5, QTableWidgetItem(f"{ci_lower:.6f}"))
            self.coeff_table.setItem(i, 6, QTableWidgetItem(f"{ci_upper:.6f}"))
            
            if p_val < 0.05:
                for j in range(7):
                    self.coeff_table.item(i, j).setBackground(QBrush(QColor(200, 230, 201)))
        
        self.coeff_table.resizeColumnsToContents()

    def display_anova(self, model, df, formula):
        try:
            anova_result = anova_lm(model)
            
            self.anova_table.setRowCount(len(anova_result))
            self.anova_table.setColumnCount(5)
            self.anova_table.setHorizontalHeaderLabels([
                "源", "自由度", "平方和", "均方", "F值"
            ])
            
            for i, (idx, row) in enumerate(anova_result.iterrows()):
                self.anova_table.setItem(i, 0, QTableWidgetItem(str(idx)))
                self.anova_table.setItem(i, 1, QTableWidgetItem(f"{row['df']:.0f}"))
                self.anova_table.setItem(i, 2, QTableWidgetItem(f"{row['sum_sq']:.6f}"))
                self.anova_table.setItem(i, 3, QTableWidgetItem(f"{row['mean_sq']:.6f}"))
                if pd.notna(row['F']):
                    self.anova_table.setItem(i, 4, QTableWidgetItem(f"{row['F']:.6f}"))
            
            self.anova_table.resizeColumnsToContents()
        except:
            pass

    def reset(self):
        self.df = None
        self.numeric_columns = []
        self.y_combo.clear()
        self.x_list.clear()
        self.data_info.clear()
        self.output_text.clear()
        self.model_summary_table.setRowCount(0)
        self.coeff_table.setRowCount(0)
        self.anova_table.setRowCount(0)


def main():
    app = QApplication(sys.argv)
    window = LinearRegressionTool()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
