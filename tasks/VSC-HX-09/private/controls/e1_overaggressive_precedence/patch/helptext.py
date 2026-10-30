# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""`help [COMMAND]`: usage summary.  The README is the full specification."""

USAGE = {
    "clock": ["clock set N", "clock advance DURATION", "clock show"],
    "secret": ["secret add NAME VALUE", "secret list"],
    "attr": ["attr set SUBJECT KEY VALUE", "attr show SUBJECT"],
    "set": ["set create NAME [parent=P] [mode=standard|admin]", "set list", "set show NAME",
            "set parent NAME PARENT|-"],
    "rule": ["rule add SET EFFECT ACTION RESOURCE [when CONDITION]", "rule del RID"],
    "cond": ["cond define NAME EXPR", "cond list"],
    "eval": ["eval EXPR"],
    "check": ["check SET SUBJECT ACTION RESOURCE [KEY=VALUE ...]"],
    "explain": ["explain SET SUBJECT ACTION RESOURCE [KEY=VALUE ...]"],
    "approve": ["approve request SUBJECT ACTION RESOURCE DURATION",
                "approve grant AID APPROVER", "approve revoke AID",
                "approve extend AID DURATION", "approve list"],
    "log": ["log show [N]", "log filter KEY=VALUE ...", "log replay SEQ", "log retain N"],
    "report": ["report text|json|csv|html [TEMPLATE]"],
    "template": ["template set NAME TEXT", "template list"],
    "bundle": ["bundle export SET", "bundle import SET   (block up to .end)"],
    "stats": ["stats"],
    "lint": ["lint SET"],
    "whatif": ["whatif SET_A SET_B   (block up to .end)"],
    "verify": ["verify"],
    "help": ["help [COMMAND]"],
}


def help_lines(topic=None):
    if topic is None:
        lines = []
        for name in sorted(USAGE):
            lines.extend("USAGE " + u for u in USAGE[name])
        return lines
    if topic not in USAGE:
        return ["no help for %s" % topic]
    return ["USAGE " + u for u in USAGE[topic]]
