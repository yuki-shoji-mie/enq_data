import streamlit as st
import pandas as pd
from scipy import stats
import io

# ページの設定
st.set_page_config(page_title="アンケート統計解析ツール", layout="wide")

st.title("📊 アンケートクロス集計・カイ二乗検定ツール")
st.write("アップロードされた集計表から、属性間の有意差（カイ二乗検定）を自動計算します。")

# 1. ファイルアップロード
uploaded_file = st.file_uploader("クロス集計後のCSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # エンコーディング対応
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='cp932')

    st.subheader("アップロードデータの確認")
    st.dataframe(df.head())

    # 解析用カラムの特定（QID, questions, choices, total 以外を属性カラムとみなす）
    base_cols = ['QID', 'questions', 'choices', 'total']
    attr_cols = [c for c in df.columns if c not in base_cols]

    if not attr_cols:
        st.error("比較対象となる属性カラム（年齢区分など）が見つかりません。")
    else:
        st.info(f"比較属性: {', '.join(attr_cols)}")

        all_results = []
        
        # 2. 設問（QID）ごとにループして検定
        unique_qids = df['QID'].unique()

        for qid in unique_qids:
            # 該当設問のデータを抽出
            q_data = df[df['QID'] == qid].copy()
            
            # 検定用の度数データ（'全体'行を除いた、選択肢ごとの属性カウント）
            test_data = q_data[q_data['choices'] != '全体'][attr_cols].values
            
            p_value = None
            sig_mark = ""

            # 有効なデータがある場合のみ検定実施
            if test_data.size > 0 and test_data.sum() > 0:
                try:
                    # カイ二乗検定の実行
                    # 全て0の列や行があるとエラーになるためtry-exceptで保護
                    chi2, p, dof, expected = stats.chi2_contingency(test_data)
                    p_value = p
                    
                    # 有意確率の判定
                    if p <= 0.01:
                        sig_mark = "***"
                    elif p <= 0.05:
                        sig_mark = "**"
                    elif p <= 0.10:
                        sig_mark = "*"
                except Exception as e:
                    sig_mark = "検定不可"

            # 結果の付与（その設問の全行にp値と印を付ける）
            q_data['p値'] = p_value
            q_data['有意水準'] = sig_mark
            all_results.append(q_data)

        # 3. 全結果の統合
        result_df = pd.concat(all_results)

        st.subheader("📈 検定結果付き集計表")
        st.dataframe(result_df)

        # 4. ダウンロード機能
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="✅ 検定結果をCSVでダウンロード",
            data=csv_buffer.getvalue(),
            file_name=f"cross_tab_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

else:
    st.info("CSVファイルをアップロードすると、解析が始まります。")
    st.markdown("""
    ### 想定しているCSVの形式
    以下のカラム名が含まれていることを想定しています：
    - `QID`: 設問番号
    - `questions`: 設問文
    - `choices`: 選択肢（'全体'という名前の合計行が含まれていてもOK）
    - `total`: 合計数
    - `属性カラム1, 2...`: 年齢区分や地域など、比較したいカテゴリ
    """)
