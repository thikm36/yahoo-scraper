import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import os
import pandas as pd
import shutil
from urllib.parse import urlparse, quote  # 💡 quoteを追加！

st.set_page_config(page_title="ヤフオクライバルチェックツール", page_icon="🏺")
st.title("🏺 ヤフオクスクレイパー")

# 💡 キーワード入力欄
keyword = st.text_input( "ハイゼットトラック S500 マッドガード")

# 範囲指定
col1, col2 = st.columns(2)
with col1:
    start_page = st.number_input("開始ページ", min_value=1, value=1)
with col2:
    end_page = st.number_input("終了ページ", min_value=1, value=50)

run_button = st.button("スクレイピング開始！")

if 'results_df' not in st.session_state:
    st.session_state.results_df = None

if run_button:
    if start_page > end_page:
        st.error("開始ページは終了ページ以下にしてくれ！")
    else:
        img_folder = "product_images"
        if os.path.exists(img_folder):
            shutil.rmtree(img_folder)
        os.makedirs(img_folder)
        
        results = []
        total_count = 0
        progress_bar = st.progress(0)
        
        # 💡 日本語をURL安全な形式に変換
        encoded_keyword = quote(keyword)
        
        for page in range(start_page, end_page + 1):
            st.write(f"【{page}ページ目】{keyword} を解析中...")
            start_item = (page - 1) * 100 + 1
            # 💡 ここにencoded_keywordを組み込む
            url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_keyword}&s1=cbids&o1=a&n=100&b={start_item}"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('.Product') 
            
            if not items:
                st.warning(f"{page}ページ目は商品がないぜ！")
                break
                
            for item in items:
                title_tag = item.select_one('.Product__titleLink')
                price_tag = item.select_one('.Product__priceValue')
                img_tag = item.select_one('.Product__imageData')
                link_tag = item.select_one('a')
                bonus_tag = item.select_one('.Product__bonus')
                
                if title_tag and price_tag and link_tag:
                    price_str = price_tag.text.strip().replace('円', '').replace(',', '').replace('即決', '').strip()
                    price_int = int(price_str) if price_str.isdigit() else 0
                    seller_id = bonus_tag.get('data-auction-auc-seller-id', '不明') if bonus_tag else '不明'
                    
                    total_count += 1
                    
                    if img_tag and img_tag.has_attr('src'):
                        try:
                            auction_id = link_tag['data-auction-id']
                            img_url = img_tag['src']
                            save_name = f"{total_count:03d}_{auction_id}_{os.path.basename(urlparse(img_url).path)}"
                            with open(os.path.join(img_folder, save_name), 'wb') as f:
                                f.write(requests.get(img_url).content)
                        except:
                            pass
                    
                    results.append({"商品名": title_tag.text.strip(), "価格": price_int, "出品者ID": seller_id, "URL": title_tag['href']})
            
            progress_bar.progress((page - start_page + 1) / (end_page - start_page + 1))
            time.sleep(2)

        st.session_state.results_df = pd.DataFrame(results)
        st.success(f"全 {total_count} 件の取得完了だぜ！")

if st.session_state.results_df is not None:
    st.dataframe(st.session_state.results_df)
    csv = st.session_state.results_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("CSVをダウンロード", csv, "results.csv", "text/csv")
    shutil.make_archive("product_images", 'zip', "product_images")
    with open("product_images.zip", "rb") as fp:
        st.download_button("画像ZIPをダウンロード", fp, "images.zip", "application/zip")
