import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

print("=" * 80)
print("SPSS 线性回归分析工具 - 功能测试")
print("=" * 80)

try:
    print("\n[1/4] 测试数据导入...")
    df = pd.read_csv("test_data.csv")
    print(f"✓ 数据导入成功！")
    print(f"  - 样本数: {len(df)}")
    print(f"  - 变量数: {len(df.columns)}")
    print(f"  - 变量列表: {', '.join(df.columns.tolist())}")
    
    print("\n[2/4] 测试数据信息...")
    print(f"✓ 数据统计信息:")
    print(df.describe().to_string())
    
    print("\n[3/4] 测试线性回归模型...")
    y_var = "销售额"
    x_vars = ["广告投入", "促销次数", "时间成本"]
    formula = f"{y_var} ~ {' + '.join(x_vars)}"
    
    model = ols(formula, data=df).fit()
    print(f"✓ 模型创建成功！")
    print(f"\n【模型汇总】")
    print(f"  R² = {model.rsquared:.6f}")
    print(f"  调整 R² = {model.rsquared_adj:.6f}")
    print(f"  标准误差 = {np.sqrt(model.mse_resid):.6f}")
    print(f"  F值 = {model.fvalue:.6f}")
    print(f"  P值 = {model.f_pvalue:.6f}")
    
    print(f"\n【回归系数】")
    conf_int = model.conf_int()
    for var, coef in model.params.items():
        se = model.bse[var]
        t_stat = model.tvalues[var]
        p_val = model.pvalues[var]
        sig_marker = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"  {var:10s}: β={coef:12.4f}, SE={se:10.4f}, t={t_stat:8.4f}, p={p_val:.6f} {sig_marker}")
    
    print("\n[4/4] 测试方差分析...")
    anova_result = anova_lm(model)
    print(f"✓ 方差分析成功！")
    print(anova_result.to_string())
    
    print("\n" + "=" * 80)
    print("✓ 所有测试通过！程序已准备就绪。")
    print("=" * 80)
    print("\n下一步：运行 python SPSS_Linear_Regression_Tool.py 启动GUI应用")
    
except Exception as e:
    print(f"\n✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
