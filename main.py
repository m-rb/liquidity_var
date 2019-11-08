import pandas as pd
#from sklearn.covariance import ShrunkCovariance
import numpy as np
from scipy.stats import norm

class faang():

        def __init__(self):
            self.bid = pd.read_excel('quotes.xlsx', sheet_name='bid', sep=";",index_col=0, na_values=0).interpolate(method='linear')
            self.ask = pd.read_excel('quotes.xlsx', sheet_name='ask', sep=";",index_col=0, na_values=0).interpolate(method='linear')
            self.mid = ((self.bid + self.ask) / 2).interpolate(method='linear')
            self.relative_spread = (self.ask - self.bid)/self.mid

        def handle_returns(self):
            self.log_rets = np.log(1 + self.mid.pct_change(-1))

        def handle_covariance_matrix(self, model = ''):
            """
            Parameters
            model: if '' the covariance matrix will be equally weighted; if 'ewma', more weight will be given to recent observations
            """
            if model == 'ewma':
                self.cov = np.array(self.log_rets[::-1].ewm(alpha=1-0.94).cov()[-len(self.log_rets.columns):].reset_index(drop=True))
            else: ##constant vol
                self.cov = np.cov(log_rets.values, rowvar=False)
                if [eigenvalue < 0 for eigenvalue in np.linalg.eigvals(self.cov)] == False:
                    print('Some eigenvalues are negative.'
                          'The sample covariance matrix is not positive definite.'
                          'Try to use some shrinkage method')
                    #reg_cov = ShrunkCovariance().fit(cov) in case you need apply some shrinkage method to your sample covariance matrix

        def value_at_risk(self, confidence_interval,ptf_value):
            """
            Parameters
            confidence_interval: int or float
            ptf_value: int or float
            """
            self.ptf_value = ptf_value
            self.z_score = norm.ppf(confidence_interval)
            portfolio_comp = np.random.rand(5)
            self.portfolio_comp = portfolio_comp/np.sum(portfolio_comp,axis=0) * self.ptf_value
            self.portfolio_vol = np.sqrt(portfolio_comp.T @ self.cov @ portfolio_comp)
            self.var = self.z_score * self.portfolio_vol * ptf_value
            return self.var, self.var/self.ptf_value

        def liquidity_adjusted_value_at_risk(self,position_holding_in_days):
            """
            Parameters
            position_holding_in_days: int
            """
            correction = self.z_score #around 2 and 4 according to most of bibliography (mainly jorion) -> spreads follow a normal distribution and we will use the same confidence_interval as VaR
            self.relative_spread.plot() #have a cool overview on the portfolio spreads
            self.cost_of_liquidity = \
            1/2 * np.sum(
                        (self.portfolio_comp * (np.mean(self.relative_spread[0:position_holding_in_days-1]) \
                        + correction * np.std(self.relative_spread[0:position_holding_in_days-1]))), axis=0) \
                        + (self.portfolio_comp @ np.cov(self.relative_spread, rowvar=False) @ self.portfolio_comp.T) * correction
            self.lvar = self.var + self.cost_of_liquidity
            return self.lvar

if __name__ == "__main__":
    object = faang()
    object.handle_returns()
    object.handle_covariance_matrix(model = 'ewma')
    object.value_at_risk(confidence_interval=0.99, ptf_value=1000000)
    object.liquidity_adjusted_value_at_risk(position_holding_in_days=252)
    print(object.var)
    print(object.lvar)
    print('Taking into account Liquidity Risk the calculated (L)VaR increases by:' + ' ' + str((object.lvar - object.var)/object.var * 100) + '%')
