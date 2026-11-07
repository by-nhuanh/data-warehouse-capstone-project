import os
from pathlib import Path
import streamlit as st
import plotly.express as px
from data_access import connect,query,application_sql,PERIOD_SQL

st.set_page_config(page_title='Home Credit • Giám sát rủi ro',layout='wide')
st.markdown('<style>.block-container{padding-top:1.5rem}div[data-testid="stMetric"]{background:#f4f6f8;padding:16px;border:1px solid #dae0e6;border-radius:6px}</style>',unsafe_allow_html=True)
root=st.sidebar.text_input('Thư mục Data_Lakehouse_Project',os.environ.get('LAKEHOUSE_ROOT',str(Path(__file__).resolve().parents[2])))
page=st.sidebar.radio('Màn hình',['Hồ sơ tiếp nhận','Lịch sử tín dụng'])
@st.cache_resource
def source(root): return connect(root)
try: c,available=source(root)
except Exception as e: st.error(f'Không mở được nguồn dữ liệu: {e}'); st.stop()
st.sidebar.caption('Database gốc chỉ đọc • Không ghi dữ liệu')
with st.sidebar.expander('Tình trạng nguồn'):
 st.json(available)
missing=[k for k,v in available.items() if v['status']=='MISSING']
if missing: st.warning('Nguồn chưa có trong bộ tệp: '+', '.join(missing)+'. Các khối phụ thuộc sẽ không hiển thị số liệu.')
def ready(*names): return all(available.get(n,{}).get('status')=='READY' for n in names)
def metric(col,label,value,detail=''):
 col.metric(label,value); col.caption(detail)
def fmt(v,suffix=''):
 return 'N/A' if v is None or __import__('pandas').isna(v) else f'{v:,.2f}{suffix}'
def chart(df,x,y,title,kind='bar'):
 st.subheader(title)
 if df.empty: st.info('Không có dữ liệu phù hợp bộ lọc.'); return
 fig=(px.line(df,x=x,y=y,markers=True) if kind=='line' else px.bar(df,x=x,y=y,hover_data=list(df.columns)))
 fig.update_layout(height=270,margin=dict(l=10,r=10,t=10,b=10),showlegend=False)
 st.plotly_chart(fig,width='stretch')

def risk():
 st.title('Giám sát rủi ro hồ sơ tiếp nhận')
 if not ready('application_train'): st.error('Thiếu application_train'); return
 # Data are read from the actual supplied Bronze; no synthetic rows or imputation.
 app=application_sql(available)
 filters=st.columns(5)
 contract=filters[0].multiselect('Loại hợp đồng',query(c,f'select distinct NAME_CONTRACT_TYPE from ({app}) order by 1').iloc[:,0].dropna().tolist())
 ages=filters[1].multiselect('Nhóm tuổi',['<20','20–30','30–40','40–50','50–60','>60'])
 edu=filters[2].multiselect('Học vấn',query(c,f'select distinct NAME_EDUCATION_TYPE from ({app}) order by 1').iloc[:,0].dropna().tolist())
 income=filters[3].slider('Phân vị thu nhập (%)',0,100,(0,100))
 dataset=filters[4].selectbox('Tập dữ liệu',['Tất cả','Train','Test'])
 q=f"select *, -DAYS_BIRTH/365.25 age, case when AMT_INCOME_TOTAL>0 then AMT_CREDIT/AMT_INCOME_TOTAL end cti,case when AMT_GOODS_PRICE>0 then AMT_CREDIT/AMT_GOODS_PRICE end cg,case when AMT_INCOME_TOTAL>0 then AMT_ANNUITY/AMT_INCOME_TOTAL end dti from ({app}) where SK_ID_CURR is not null"
 q=f"select *,case when age<20 then '<20' when age<=30 then '20–30' when age<=40 then '30–40' when age<=50 then '40–50' when age<=60 then '50–60' else '>60' end age_group from ({q})"
 params=[]; conditions=[]
 for field,values in [('NAME_CONTRACT_TYPE',contract),('age_group',ages),('NAME_EDUCATION_TYPE',edu)]:
  if values: conditions.append(field+' in ('+','.join('?' for _ in values)+')'); params+=values
 if dataset!='Tất cả': conditions.append('dataset=?'); params.append(dataset)
 if income!=(0,100):
  lo,hi=c.execute(f'select quantile_cont(AMT_INCOME_TOTAL,{income[0]/100}),quantile_cont(AMT_INCOME_TOTAL,{income[1]/100}) from ({app}) where AMT_INCOME_TOTAL>0').fetchone()
  conditions.append('AMT_INCOME_TOTAL between ? and ?'); params += [lo,hi]
 if conditions: q='select * from ('+q+') where '+' and '.join(conditions)
 df=query(c,q,params)
 n=len(df); labeled=df[df.TARGET.isin([0,1])]
 cols=st.columns(4)
 metric(cols[0],'01 · Tổng hồ sơ',f'{n:,}',f"Train: {(df.dataset=='Train').sum():,} • Test: {(df.dataset=='Test').sum():,}")
 metric(cols[1],'02 · Tỷ lệ TARGET = 1',fmt(labeled.TARGET.mean()*100,'%'),f'{int(labeled.TARGET.sum()):,} / {len(labeled):,} có nhãn')
 metric(cols[2],'03 · CTI trung vị',fmt(df.cti.median(),' lần'))
 metric(cols[3],'04 · Credit/Goods trung vị',fmt(df.cg.median(),' lần'))
 import pandas as pd
 labeled=labeled.copy(); labeled['cg_group']=pd.cut(labeled.cg,[-float('inf'),.5,.8,1,1.2,1.5,float('inf')],labels=['≤0.5','0.5–0.8','0.8–1','1–1.2','1.2–1.5','>1.5'])
 def rates(frame,group):
  r=frame.groupby(group,observed=True).TARGET.agg(['mean','count']).reset_index();r['Tỷ lệ (%)']=r['mean']*100;return r
 a,b=st.columns(2)
 with a: chart(rates(labeled,'cg_group'),'cg_group','Tỷ lệ (%)','05 · TARGET = 1 theo Credit/Goods')
 with b: chart(rates(labeled,'age_group'),'age_group','Tỷ lệ (%)','06 · TARGET = 1 theo tuổi')
 a,b,d=st.columns(3)
 with a:
  st.subheader('07 · Cơ cấu hợp đồng')
  counts=df.groupby('NAME_CONTRACT_TYPE',dropna=False).size().reset_index(name='Hồ sơ')
  if n: st.plotly_chart(px.pie(counts,names='NAME_CONTRACT_TYPE',values='Hồ sơ'),width='stretch')
  st.dataframe(rates(labeled,'NAME_CONTRACT_TYPE'),hide_index=True)
 with b:
  st.subheader('08 · Gánh nặng trả góp')
  st.metric('DTI trung vị',fmt(df.dti.median()*100,'%'))
  st.plotly_chart(px.box(df,x='dti',points=False),width='stretch')
 with d:
  st.subheader('09 · Bao phủ nhãn')
  st.metric('Hồ sơ có nhãn',fmt(len(labeled)/n*100 if n else None,'%'))
  st.progress(len(labeled)/n if n else 0); st.caption(f'{len(labeled):,} / {n:,}')
 st.caption('TARGET phản ánh nhãn lịch sử; không phải dự báo. Không diễn giải quan hệ nhân quả. Tuổi = −DAYS_BIRTH/365.25. Phân vị thu nhập tính trên nguồn trước các bộ lọc khác.')
 if not ready('application_test'): st.info('Tổng hiện tại chỉ bao gồm Train; chưa thể nghiệm thu chỉ số tổng Train + Test và độ bao phủ nhãn toàn bộ.')
 st.download_button('Xuất hồ sơ đang lọc',df.to_csv(index=False).encode(), 'ho_so_filtered.csv','text/csv')

def history():
 st.title('Lịch sử tín dụng và hành vi thanh toán')
 f=st.columns(4)
 window=f[0].selectbox('Cửa sổ lịch sử',['Toàn bộ','6 tháng','12 tháng'])
 contracts=f[1].multiselect('Loại hợp đồng cũ',query(c,'select distinct NAME_CONTRACT_TYPE from previous_application order by 1').iloc[:,0].dropna().tolist() if ready('previous_application') else [])
 statuses=f[2].multiselect('Trạng thái CIC',['0','1','2','3','4','5','C','X'])
 late=f[3].checkbox('Chỉ khách từng trả trễ',disabled=not ready('installments_payments'))
 months={'Toàn bộ':None,'6 tháng':6,'12 tháng':12}[window]
 st.caption('Cửa sổ áp dụng ngày tương đối cho thanh toán/đơn cũ và MONTHS_BALANCE cho CIC/thẻ. Loại hợp đồng cũ xác định tập khách hàng; trạng thái CIC chỉ lọc biểu đồ CIC. Không quy đổi ngày tương đối thành lịch thực.')
 cohort='select distinct SK_ID_CURR from previous_application'
 cp=[]
 if contracts: cohort+=' where NAME_CONTRACT_TYPE in ('+','.join('?' for _ in contracts)+')';cp+=contracts
 if late:
  cohort=f'select SK_ID_CURR from ({cohort}) intersect select SK_ID_CURR from installments_payments where DAYS_ENTRY_PAYMENT>DAYS_INSTALMENT'
 restriction=f' SK_ID_CURR in ({cohort})' if ready('previous_application') and (contracts or late) else 'true'
 cols=st.columns(4)
 if ready('installments_payments'):
  period='select * from ('+PERIOD_SQL+') where '+restriction
  # Relative due-date filtering is applied before period aggregation, via source CTE.
  if months:
   period='with installments_payments as (select * from installments_payments where DAYS_INSTALMENT between ? and 0) '+period
   pp=[-months*30]+cp
  else: pp=cp
  p=query(c,period,pp); valid=p[(p.valid_dates==p.rows_count)&p.delta.notna()]
  metric(cols[0],'01 · Kỳ trả trễ',fmt((valid.delta>0).mean()*100,'%'),f'{(valid.delta>0).sum():,} / {len(valid):,} kỳ đủ ngày')
  cust=p.groupby('SK_ID_CURR').delta.max()
  metric(cols[1],'02 · Khách từng trả trễ',fmt((cust>0).mean()*100,'%'),f'{(cust>0).sum():,} / {len(cust):,} khách')
  metric(cols[2],'03 · Tiền thiếu hụt',fmt(p.shortfall.sum(min_count=1)/1e6,' triệu đơn vị nguồn'),f'{(p.shortfall>0).sum():,} kỳ thiếu')
 else:
  p=None
  for col,label in zip(cols[:3],['01 · Kỳ trả trễ','02 · Khách từng trả trễ','03 · Tiền thiếu hụt']): metric(col,label,'N/A','Thiếu installments_payments')
 if ready('previous_application'):
  sql='select count(*) n,count(*) filter(where NAME_CONTRACT_STATUS=\'Approved\') approved from previous_application where '+restriction
  args=cp.copy()
  if months: sql+=' and TRY_CAST(DAYS_DECISION AS INTEGER) between ? and 0';args += [-months*30]
  r=query(c,sql,args).iloc[0];metric(cols[3],'04 · Phê duyệt đơn cũ',fmt(r.approved/r.n*100 if r.n else None,'%'),f'{r.approved:,} / {r.n:,}')
 a,b=st.columns(2)
 with a:
  if ready('installments_payments'):
   sql='select DAYS_ENTRY_PAYMENT-DAYS_INSTALMENT delta from installments_payments where DAYS_ENTRY_PAYMENT is not null and DAYS_INSTALMENT is not null and '+restriction
   args=cp.copy()
   if months: sql+=' and DAYS_INSTALMENT between ? and 0';args += [-months*30]
   tx=query(c,sql,args);tx['Nhóm']=tx.delta.map(lambda x:'Trả sớm' if x<0 else 'Đúng hạn' if x==0 else 'Trả trễ')
   dist=tx.groupby('Nhóm').size().reset_index(name='Giao dịch');dist['Tỷ trọng (%)']=dist['Giao dịch']/len(tx)*100
   chart(dist,'Nhóm','Tỷ trọng (%)','05 · Kỷ luật thanh toán')
   st.caption('Phân vị ngày lệch: '+str(tx.delta.quantile([.5,.95,.99]).to_dict()))
  else: st.subheader('05 · Kỷ luật thanh toán');st.info('Chưa có nguồn thanh toán.')
 with b:
  if ready('bureau_balance','bureau'):
   wh=('b.SK_ID_CURR in ('+cohort+')' if contracts or late else 'true');args=cp.copy()
   if months: wh+=' and bb.MONTHS_BALANCE between ? and 0';args +=[-months+1]
   if statuses: wh+=' and cast(bb.STATUS as varchar) in ('+','.join('?' for _ in statuses)+')';args+=statuses
   cic=query(c,"select bb.MONTHS_BALANCE,100.0*count(*) filter(where cast(bb.STATUS as varchar) in ('1','2','3','4','5'))/nullif(count(*) filter(where cast(bb.STATUS as varchar) in ('0','1','2','3','4','5')),0) rate,count(*) n from bureau_balance bb join bureau b using(SK_ID_BUREAU) where "+wh+' group by 1 order by 1',args)
   chart(cic,'MONTHS_BALANCE','rate','06 · Quá hạn CIC (%)','line');st.caption('Mẫu số chỉ gồm trạng thái 0–5; C/X giữ riêng, không coi là 0. Bản ghi không ghép Bureau không tham gia tập khách hàng.')
 a,b,d=st.columns(3)
 with a:
  st.subheader('07 · TARGET theo mức dùng thẻ')
  if ready('credit_card_balance','application_train'):
   wh='AMT_CREDIT_LIMIT_ACTUAL>0 and '+restriction;args=cp.copy()
   if months: wh+=' and MONTHS_BALANCE between ? and 0';args +=[-months+1]
   cc=query(c,'select SK_ID_CURR,avg(AMT_BALANCE/AMT_CREDIT_LIMIT_ACTUAL) utilization from credit_card_balance where '+wh+' group by 1',args)
   high_utilization=(cc.utilization>.8).mean()*100
   labels=query(c,'select SK_ID_CURR,TARGET from application_train');cc=cc.merge(labels,on='SK_ID_CURR',validate='one_to_one')
   import pandas as pd
   cc['Nhóm']=pd.cut(cc.utilization,[-float('inf'),0,.3,.5,.8,1,float('inf')],labels=['≤0','0–30%','30–50%','50–80%','80–100%','>100%'])
   rr=cc.groupby('Nhóm',observed=True).TARGET.agg(['mean','count']).reset_index();rr['Tỷ lệ (%)']=rr['mean']*100
   st.plotly_chart(px.bar(rr,x='Nhóm',y='Tỷ lệ (%)',hover_data=['count']),width='stretch')
 with b:
  st.subheader('08 · Cảnh báo sớm')
  st.caption('Ngưỡng dùng thẻ >80% lấy từ wireframe; chưa được xác nhận là ngưỡng chính sách.')
  if 'cc' in locals(): st.metric('Khách dùng thẻ TB >80%',fmt(high_utilization,'%'))
  if ready('bureau'):
   debt=query(c,'select sum(TRY_CAST(AMT_CREDIT_SUM_DEBT AS DECIMAL(20,4))) debt from bureau where '+restriction,cp).iloc[0,0]
   st.metric('Dư nợ ngoài',fmt(debt/1e9,' tỷ đơn vị nguồn'))
  if ready('installments_payments'): st.metric('Ngày lệch trung vị',fmt(tx.delta.median(),' ngày'))
  st.caption('CIC hiện tại: chưa xác nhận quy ước tháng hiện tại nghiệp vụ; không suy đoán từ tháng gần nhất.')
 with d:
  st.subheader('09 · Hợp đồng cần nhắc nợ')
  if p is not None:
   reminders=p[(p.delta>0)&(p.shortfall>0)].sort_values('shortfall',ascending=False)
   st.dataframe(reminders.head(100),hide_index=True)
   st.download_button('Xuất danh sách nhắc nợ',reminders.to_csv(index=False).encode(),'nhac_no.csv','text/csv')
  else: st.info('Thiếu dữ liệu kỳ trả; chưa thể lập danh sách.')
 st.caption('Đơn vị tiền tệ Home Credit chưa được xác nhận là VNĐ; chỉ hiển thị theo đơn vị nguồn. DPD ở đây là độ trễ lịch sử thanh toán, không phải số ngày quá hạn tại ngày chạy.')
try:
 if page=='Hồ sơ tiếp nhận': risk()
 else: history()
except Exception as e:
 st.error(f'Truy vấn chưa hoàn tất: {type(e).__name__}: {e}')
 st.stop()
