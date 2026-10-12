import copy
import unittest
import numpy as np
from aimodel.calibration.data import CENTRAL, CAL
from aimodel.core.economy import simulate
from aimodel.core.employment import load_config, simulate_employment
from fetch_employment_data import decode_jsonstat


class EmploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_config()
        cls.p = {k:np.full(3,v) for k,v in CENTRAL.items()}
        cls.base = simulate(cls.p,ai=False)
        cls.ai = simulate(cls.p,ai=True,base_ratio=cls.base["dd_ratio"],base_wage=cls.base["wage"])

    def test_stock_closure_and_bounds(self):
        o=simulate_employment(self.ai,self.c,"slow")
        np.testing.assert_allclose(o["employed"]+o["unemployed"],o["supply"],atol=1e-12)
        np.testing.assert_allclose(o["supply"]+o["discouraged"],o["potential_supply"],atol=1e-12)
        np.testing.assert_allclose(o["potential_supply"].sum(-1),self.ai["lsup"],atol=1e-12)
        np.testing.assert_allclose(o["demand"].sum(-1),self.ai["ldem"],atol=1e-12)
        self.assertLess(o["max_stock_flow_residual"],1e-12)
        for key in ("employment_rate","unemployment_rate","participation_rate","rehire_rate","first_hire_rate"):
            self.assertTrue((o[key]>=0).all() and (o[key]<=100+1e-10).all(),key)

    def test_zero_adoption_has_no_artificial_ai_gap(self):
        a=simulate_employment(self.base,self.c,"persistent",ai=True)
        b=simulate_employment(self.base,self.c,"persistent",ai=False)
        for key in ("employed","hires","unemployed","discouraged","supply"):
            np.testing.assert_array_equal(a[key],b[key])

    def test_initial_unemployment_reconciles_macro(self):
        o=simulate_employment(self.base,self.c,"reference",ai=False)
        np.testing.assert_allclose(o["unemployed"][0].sum(-1)/o["supply"][0].sum(-1),
                                   np.broadcast_to(CAL["u_star"],(3,3)),atol=1e-12)

    def test_no_vacancies_means_no_hiring(self):
        m={k:v.copy() if isinstance(v,np.ndarray) else v for k,v in self.base.items()}
        m["ldem"][1:]=0
        o=simulate_employment(m,self.c,"reference",ai=False)
        np.testing.assert_array_equal(o["hires"][1:],0)
        np.testing.assert_array_equal(o["employed"][1:],0)
        self.assertTrue((o["job_cuts"][1].sum(-1)>0).all())

    def test_no_automatic_rematching(self):
        c=copy.deepcopy(self.c)
        c["first_hire_probability"]=[0]*4;c["rehire_probability"]=[0]*4
        o=simulate_employment(self.base,c,"reference",ai=False)
        np.testing.assert_array_equal(o["hires"],0)
        self.assertTrue((o["vacancies"][2].sum(-1)>0).all())
        self.assertTrue((o["unemployed"][2].sum(-1)>0).all())

    def test_discouragement_does_not_erase_broad_nonemployment(self):
        m={k:v.copy() if isinstance(v,np.ndarray) else v for k,v in self.base.items()}
        m["ldem"][1:]=0
        c=copy.deepcopy(self.c);c["discouragement_probability"]=[0]*4
        c["return_probability"]=[0]*4
        a=simulate_employment(m,c,"reference",ai=False)
        c["discouragement_probability"]=[.5]*4
        b=simulate_employment(m,c,"reference",ai=False)
        np.testing.assert_allclose(a["broad_nonemployment"][1:],b["broad_nonemployment"][1:],atol=1e-12)
        self.assertTrue((b["supply"][2].sum(-1)<a["supply"][2].sum(-1)).all())

    def test_cohorts_age_and_retire(self):
        o=simulate_employment(self.base,self.c,"reference",ai=False)
        self.assertTrue((o["age65_exits"][1,:,:,3]>0).all())
        np.testing.assert_array_equal(o["age65_exits"][:,:,:,:3],0)
        self.assertFalse(np.allclose(o["population"][0,:,:,0]/o["population"][0].sum(-1),
                                    o["population"][-1,:,:,0]/o["population"][-1].sum(-1)))

    def test_sparse_jsonstat_keeps_zero_and_flags(self):
        d=dict(id=["age","time"],size=[2,2],dimension={
            "age":{"category":{"index":{"a":0,"b":1}}},
            "time":{"category":{"index":{"2024":0,"2025":1}}}},
            value={"0":0,"3":10},status={"3":"b"})
        rows=list(decode_jsonstat(d))
        self.assertEqual(rows,[dict(age="a",time="2024",value=0,flag=""),
                               dict(age="b",time="2025",value=10,flag="b")])

    def test_observed_proxy_reconciles_supply(self):
        from pathlib import Path
        p=Path(__file__).resolve().parents[1]/"config/employment_eu_proxy.json"
        if not p.exists():
            self.skipTest("Observed data have not been downloaded")
        o=simulate_employment(self.ai,load_config(p),"reference")
        np.testing.assert_allclose(o["potential_supply"].sum(-1),self.ai["lsup"],atol=1e-12)
        self.assertLess(o["max_stock_flow_residual"],1e-12)


    def test_unit_hazard_scale_is_neutral(self):
        c=copy.deepcopy(self.c);c["hire_hazard_scale"]=[1.0,1.0,1.0]
        a=simulate_employment(self.ai,self.c,"slow");b=simulate_employment(self.ai,c,"slow")
        for key in ("employed","hires","unemployed","discouraged"):
            np.testing.assert_array_equal(a[key],b[key])

    def test_consistency_calibration_hits_structural_rate(self):
        from pathlib import Path
        p=Path(__file__).resolve().parents[1]/"config/employment_eu_proxy.json"
        c=load_config(p)
        if "hire_hazard_scale" not in c:
            self.skipTest("Consistency calibration not run")
        base=simulate({k:np.full(1,v) for k,v in CENTRAL.items()},ai=False)
        e=simulate_employment(base,c,"reference",ai=False)
        u=(e["unemployed"].sum(-1)/e["supply"].sum(-1))[1:,0].mean(0)
        np.testing.assert_allclose(u,CAL["u_star"],atol=1e-4)


class CoupledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_config()
        cls.p = {k:np.full(3,v) for k,v in CENTRAL.items()}

    def test_own_unemployment_path_is_neutral(self):
        b=simulate(self.p,ai=False)
        a=simulate(self.p,ai=True,base_ratio=b["dd_ratio"],base_wage=b["wage"])
        a2=simulate(self.p,ai=True,base_ratio=b["dd_ratio"],base_wage=b["wage"],ur_path=a["unemp"])
        for key in ("Y","wage","debt_ratio","unemp","Cg"):
            np.testing.assert_array_equal(a[key],a2[key])

    def test_coupled_pair_converges_and_closes_accounts(self):
        from aimodel.core.coupled import coupled_pair, age_unemployment
        r=coupled_pair(self.p,self.c,"reference")
        self.assertTrue(r["info_base"]["converged"] and r["info_ai"]["converged"])
        for world,emp in (("base","emp_base"),("ai","emp_ai")):
            self.assertLess(np.abs(r[world]["residual"]).max(),1e-12)
            np.testing.assert_allclose(r[world]["unemp"],age_unemployment(r[emp],r[world]),atol=1e-8)
            self.assertLess(r[emp]["max_stock_flow_residual"],1e-12)


if __name__=="__main__":
    unittest.main()
