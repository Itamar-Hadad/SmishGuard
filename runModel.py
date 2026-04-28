from MLsmish import predict_message

messages = [
    """Highway 6
Warning: You must pay a balance of 14.98 ₪ immediately to avoid double charges / legal proceedings / additional fees: https://t.co/8X4a9MWzNU""",
    """Hello,
If you do not take action to settle your debts urgently,
we will be forced to transfer the handling to other legal proceedings.
Click here: did.li/-Kvish6-Pay""",
    """Neta, you have a special greeting from Eran Bar Insurance Agency in honor of your birthday! To view >>
https://persovid.treepodia.com/l/14135601FnFuEyX""",
    """There is an debt for travel on Highway 6 North. The debt has been transferred for enforcement (collections/legal execution). You can settle the payment:
https://m-r.pw/OuSt
Thank you, Highway 6""",
    """Alert about an irregularity in the account status: Immediate action is required regarding an existing debt. To settle the debt immediately, enter the link: https://did.li/Ss3Iw or call 6116. Further delay may lead to legal action.""",
    "I will call you when i get home"
]

# messages = ["An unpaid balance for travel on Highway 6 North has been transferred to enforcement for collection. You can settle the payment here: https://m-r.pw/OuSt Thank you, Highway 6", 
#             """“Leumi Bank, good morning,
# This is a message from Leumi Bank. We have identified unusual activity in your account. Therefore, for your safety, we have temporarily blocked the account and it is not possible to perform actions in it.
# To reactivate your account, please log in via the following link:
# https://leumi-bank.com/leumi-credit2

# Sincerely,
# Leumi Bank.”""",
# """Hello,
# To ensure the security of your account at Leumi Bank, please confirm your login details using the link below:
# https://did.li/leumi-il
# Failure to complete the verification may result in your account being restricted.
# Thank you,
# Leumi Bank.""", 
# """Leumi Bank, hello,
# This is a message from Leumi Bank. We have identified unusual activity in your account. Therefore, for your safety, we have temporarily blocked the account and it is not possible to perform actions in it.
# To reactivate your account, please log in via the following link:
# http://bit.ly/Bank-Leumi-13
# Sincerely,
# Leumi Bank.""", 
# """Dear insured,
# Dental claim number 318699 has been approved and will be paid by bank transfer.
# Information is also available for you on the personal information website:
# https://www.menoramivt.co.il/wps/myportal/personal/myclaims
# Best regards,
# Health Claims Department, Menora Mivtachim Insurance Ltd.
# Subject to company records (T.L.H).""", 
# """Hello,
# During the month of 01/26, your account ending with the digits 998 was charged as follows:
# Fees totaling 0.00 NIS.
# Interest totaling 0.00 NIS.
# The fee amounts may include fees charged quarterly or annually.
# The interest amounts may include interest charged quarterly or for a defined period.
# You can view the description and detailed breakdown of the amounts on the bank’s website and app under the ‘Reports and Certificates’ tab, or via online mail if you are subscribed to the service. If the account is not connected to the bank’s digital channels, the details are sent via Israel Post.
# Best regards,
# Otzar HaHayal, International Bank.
# Message 093-040.""",
# """Hello,
# During the month of 01/26, your account ending with the digits 998 was charged as follows:
# Fees totaling 0.00 NIS.
# Interest totaling 0.00 NIS.
# The fee amounts may include fees charged quarterly or annually.
# The interest amounts may include interest charged quarterly or for a defined period.
# You can view the description and detailed breakdown of the amounts on the bank’s website and app under the ‘Reports and Certificates’ tab, or via online mail if you are subscribed to the service. If the account is not connected to the bank’s digital channels, the details are sent via Israel Post.
# Best regards,
# Otzar HaHayal, International Bank.
# Message 093-040."""]



#spam messages!!!!!!!

# messages = [
#     """Neta, enjoy account credit for you and your bestie! 😇
# Invite friends to the IBI Trade app through your personal area and receive ₪700 in account credit to your trading account! Your friend who joins will enjoy ₪300 in account credit in their new trading account (advertisement).
# To share the link with friends: https://cloud.mc.ibi.co.il/sms_tr?l=app-ref&j=ref-blast&k=s18-1-a
# *Subject to the promotion terms on the website.
# To unsubscribe, send 01 to 0539001055""",
#     """Hi Neta,
# We’ve launched new gummies that will help you get through your period days more easily and in balance,
# with 10% off and free shipping 🧚‍♀️ Don’t miss out >>
# https://fls.cx/3DRbuMe
# Valid until April 30 at midnight | While supplies last | On the product ‘Break Free’ | Cannot be combined with other promotions or discounts | Excludes semi-annual and annual bundles | Minimum 1,000 units in stock | Errors and omissions excepted
# Mayven (Nakash Group Ltd.)
# Address: Kehilat Venezia 8, Tel Aviv
# Phone: 03-6375525
# To unsubscribe, reply “REMOVE” to 0534513523"""
# ]

for msg in messages:
    label, confidence = predict_message(msg)
    print(f"[{label.upper()} | {confidence:.1%}] {msg[:80]}{'...' if len(msg) > 80 else ''}")
    print()
