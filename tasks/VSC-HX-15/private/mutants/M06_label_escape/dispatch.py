# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Reads a command stream and routes each line to its handler."""
import cmd_data
import cmd_setup
import cmd_views
import lexer
from errors import CmdError

HANDLERS = {
    "set": cmd_setup.do_set,
    "config": cmd_setup.do_config,
    "site": cmd_setup.do_site,
    "route": cmd_setup.do_route,
    "ship": cmd_setup.do_ship,
    "profiles": cmd_setup.do_profiles,
    "plan": cmd_setup.do_plan,
    "handoff": cmd_setup.do_handoff,
    "read": cmd_data.do_read,
    "arrive": cmd_data.do_arrive,
    "shift": cmd_data.do_shift,
    "prune": cmd_data.do_prune,
    "window": cmd_data.do_window,
    "timeline": cmd_data.do_timeline,
    "verify": cmd_data.do_verify,
    "rollup": cmd_views.do_rollup,
    "excursions": cmd_views.do_excursions,
    "alerts": cmd_views.do_alerts,
    "sla": cmd_views.do_sla,
    "rank": cmd_views.do_rank,
    "find": cmd_views.do_find,
    "legs": cmd_views.do_legs,
    "report": cmd_views.do_report,
    "export": cmd_views.do_export,
    "describe": cmd_views.do_describe,
    "plans": cmd_views.do_plans,
    "custody": cmd_views.do_custody,
    "fleet": cmd_views.do_fleet,
    "audit": cmd_views.do_audit,
    "stats": cmd_views.do_stats,
    "forecast": cmd_views.do_forecast,
    "exposure": cmd_views.do_exposure,
    "board": cmd_views.do_board,
    "histogram": cmd_views.do_histogram,
    "compare": cmd_views.do_compare,
}

HELP_LINES = [
    "set KEY VALUE            change a setting (hold keep gap cap slack spike)",
    "config                   show the settings",
    "site add CODE NAME       register a depot or stop",
    "site list                list the sites",
    "site export              write the sites as tab-separated text",
    "route add ID CODE...     define a route of two or more stops",
    "profiles                 list the cargo classes and their bands",
    "ship add ID LABEL route=R [class= min= max= maxexc= cap= hmax= skew= offset=]",
    "ship edit ID options     change a shipment",
    "ship show ID             show a shipment",
    "ship list                list the shipments",
    "ship rename ID LABEL     change the label",
    "ship remove ID           delete a shipment and its readings",
    "read ID t= temp= [hum=]  store one reading",
    "load ID                  read comma-separated rows up to 'end load'",
    "arrive ID stop=N t=      record an arrival at a stop",
    "plan ID stop=N t=        record the planned arrival at a stop",
    "plans ID                 list planned arrivals and delays",
    "handoff ID PARTY t=      record a custody handoff",
    "custody ID               list the custody chain",
    "verify ID N sig=         check a handoff signature",
    "shift ID seconds=N       move every reading of a shipment in time",
    "prune now= [dry=yes]     drop readings older than the keep window",
    "window ID [from= to=]    list readings in a range",
    "timeline ID [from= to=]  list readings with day and clock time",
    "describe ID [from= to=]  summary statistics",
    "forecast ID [minutes=N]  straight-line projection of the temperature",
    "exposure ID              degree-minutes spent outside the band",
    "board                    one line per shipment",
    "histogram ID [step=N]    readings per temperature bucket",
    "compare ID ID            two shipments side by side",
    "rollup ID                hourly statistics",
    "excursions ID            runs of out-of-band readings",
    "alerts [ID] [kind=K]     excursion, gap, spike, humid and late alerts",
    "sla ID                   share of in-band readings",
    "rank [by=sla|exposure|alerts]  shipments, worst first",
    "find TEXT                search labels",
    "legs ID                  per-leg view of a journey",
    "report ID                summary of one shipment",
    "export ID|all            write a shipment (or all) as tab-separated text",
    "import                   read a block written by export",
    "fleet                    counts over all shipments",
    "audit [N]                the last N command lines",
    "stats                    counts of everything",
    "help                     this text",
]

BLOCKS = {"import": ("end export", cmd_data.do_import), "load": ("end load", cmd_data.do_load)}


def do_help(world, pos, opts):
    for line in HELP_LINES:
        world.emit(line)


def take_block(lines, i, terminator):
    """Collects raw lines up to and including the terminator; returns (block, next index, closed)."""
    block = []
    while i < len(lines):
        text = lines[i].rstrip("\r")
        i += 1
        if text == terminator:
            return block, i, True
        block.append(text)
    return block, i, False


def run(world, text):
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        world.audit.record(line)
        try:
            words = lexer.tokenize(line)
            name = words[0].text
            pos, opts = lexer.split_args(words[1:])
            if name == "import" or name == "load":
                terminator, handler = BLOCKS[name]
                block, i, closed = take_block(lines, i, terminator)
                if not closed:
                    raise CmdError("block is not closed")
                if name == "import":
                    handler(world, block + [terminator])
                else:
                    handler(world, pos, block)
            elif name == "help":
                do_help(world, pos, opts)
            elif name in HANDLERS:
                HANDLERS[name](world, pos, opts)
            else:
                raise CmdError("unknown command %s" % name)
        except CmdError as exc:
            world.emit("error: %s" % exc)
