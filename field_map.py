"""
Encompass field mapping.

Each entry maps a logical contract field to one or more Encompass field IDs.
Encompass field IDs come from right-clicking a field in the desktop client
(or pressing Ctrl+G to "Go to Field").
"""

FIELD_MAP = {
    "seller_1_name":         ["638"],
    "seller_2_name":         ["VEND.X412"],
    "seller_3_name":         ["Seller3.Name"],
    "seller_4_name":         ["Seller4.Name"],
    "closing_date":          ["748"],
    "due_diligence_date":    ["CX.APPRAISAL.CONTIN", "CX.FINANCE.CONTIN"],
    "listing_agent_name":    ["VEND.X150"],
    "listing_agent_company": ["VEND.X144"],
    "listing_agent_email":   ["VEND.X152"],
    "listing_agent_phone":   ["VEND.X151"],
    "transaction_costs":     ["4795"],
    "earnest_plus_dd_fee":   ["URLAROA0103"],
}
