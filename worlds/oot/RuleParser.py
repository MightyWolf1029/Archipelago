import ast
from collections import defaultdict
import logging

from .OoTR.ItemList import item_table
from .Location import OOTLocation
from .Region import OOTRegion
from BaseClasses import CollectionState as State

from worlds.generic.Rules import set_rule

from .OoTR.RuleParser import Rule_AST_Transformer, escaped_items, event_name, allowed_globals, rule_aliases, \
    nonaliases, load_aliases

def __init__(self, world, player):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``__init__`` function.
    Takes an additional argument ``player`` and uses it in ``kwarg_defaults``, which
    is now a class attribute.
    """
    self.world = world
    self.events = set()
    # map Region -> rule ast string -> item name
    self.replaced_rules = defaultdict(dict)
    # delayed rules need to keep: region name, ast node, event name
    self.delayed_rules = []
    # lazy load aliases
    if not rule_aliases:
        load_aliases()
    # final rule cache
    self.rule_cache = {}
    ########################
    # Begin AP modified code
    self.player = player
    self.kwarg_defaults = {}  # otherwise this gets contaminated between players
    self.kwarg_defaults['player'] = self.player
    # End AP modified code
    ########################

def visit_Name(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_Name`` function.
    Uses the ``kwarg_defaults`` class attribute. Uses the ``player`` class attribute
    as an argument when running ``ast.Call``.
    """
    if node.id in dir(self):
        return getattr(self, node.id)(node)
    elif node.id in rule_aliases:
        args, repl = rule_aliases[node.id]
        if args:
            raise Exception('Parse Error: expected %d args for %s, not 0' % (len(args), node.id),
                    self.current_spot.name, ast.dump(node, False))
        return self.visit(ast.parse(repl, mode='eval').body)
    elif node.id in escaped_items:
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='state', ctx=ast.Load()),
                attr='has',
                ctx=ast.Load()),
            ########################
            # Begin AP modified code
            args=[ast.Str(escaped_items[node.id]), ast.Constant(self.player)],
            # End AP modified code
            ########################
            keywords=[])
    elif node.id in self.world.__dict__:
        # Settings are constant
        return ast.parse('%r' % self.world.__dict__[node.id], mode='eval').body
    elif node.id in State.__dict__:
        return self.make_call(node, node.id, [], [])
    ########################
    # Begin AP modified code
    elif node.id in self.kwarg_defaults or node.id in allowed_globals:
    # End AP modified code
    ########################
        return node
    elif event_name.match(node.id):
        self.events.add(node.id.replace('_', ' '))
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='state', ctx=ast.Load()),
                attr='has',
                ctx=ast.Load()),
            ########################
            # Begin AP modified code
            args=[ast.Str(node.id.replace('_', ' ')), ast.Constant(self.player)],
            # End AP modified code
            ########################
            keywords=[])
    else:
        raise Exception('Parse Error: invalid node name %s' % node.id, self.current_spot.name, ast.dump(node, False))

def visit_Str(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_Str`` function.
    Uses the ``player`` class attribute as an argument when running ``ast.Call``.
    """
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='state', ctx=ast.Load()),
            attr='has',
            ctx=ast.Load()),
        ########################
        # Begin AP modified code
        args=[ast.Str(node.s), ast.Constant(self.player)],
        # End AP modified code
        ########################
        keywords=[])

def visit_Tuple(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_Tuple`` function.
    Uses the ``player`` class attribute as an argument when running ``ast.Call``.
    """
    if len(node.elts) != 2:
        raise Exception('Parse Error: Tuple must have 2 values', self.current_spot.name, ast.dump(node, False))

    item, count = node.elts

    if not isinstance(item, (ast.Name, ast.Str)):
        raise Exception('Parse Error: first value must be an item. Got %s' % item.__class__.__name__, self.current_spot.name, ast.dump(node, False))
    iname = item.id if isinstance(item, ast.Name) else item.s

    if not (isinstance(count, ast.Name) or isinstance(count, ast.Num)):
        raise Exception('Parse Error: second value must be a number. Got %s' % item.__class__.__name__, self.current_spot.name, ast.dump(node, False))

    if isinstance(count, ast.Name):
        # Must be a settings constant
        count = ast.parse('%r' % self.world.__dict__[count.id], mode='eval').body

    if iname in escaped_items:
        iname = escaped_items[iname]

    if iname not in item_table:
        self.events.add(iname)

    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='state', ctx=ast.Load()),
            attr='has',
            ctx=ast.Load()),
        ########################
        # Begin AP modified code
        args=[ast.Str(iname), ast.Constant(self.player), count],
        # End AP modified code
        ########################
        keywords=[])

def visit_Call(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_Call`` function.
    Get elements in ``world.__dict__`` as ``Constant`` instead of ``Attribute``.
    """
    if not isinstance(node.func, ast.Name):
        return node

    if node.func.id in dir(self):
        return getattr(self, node.func.id)(node)
    elif node.func.id in rule_aliases:
        args, repl = rule_aliases[node.func.id]
        if len(args) != len(node.args):
            raise Exception('Parse Error: expected %d args for %s, not %d' % (len(args), node.func.id, len(node.args)),
                    self.current_spot.name, ast.dump(node, False))
        # straightforward string manip
        for arg_re, arg_val in zip(args, node.args):
            if isinstance(arg_val, ast.Name):
                val = arg_val.id
            elif isinstance(arg_val, ast.Constant):
                val = repr(arg_val.value)
            elif isinstance(arg_val, ast.Str):
                val = repr(arg_val.s)
            else:
                raise Exception('Parse Error: invalid argument %s' % ast.dump(arg_val, False),
                        self.current_spot.name, ast.dump(node, False))
            repl = arg_re.sub(val, repl)
        return self.visit(ast.parse(repl, mode='eval').body)

    new_args = []
    for child in node.args:
        if isinstance(child, ast.Name):
            if child.id in self.world.__dict__:
                ########################
                # Begin AP modified code
                child = ast.Constant(getattr(self.world, child.id))
                # End AP modified code
                ########################
            elif child.id in rule_aliases:
                child = self.visit(child)
            elif child.id in escaped_items:
                child = ast.Str(escaped_items[child.id])
            else:
                child = ast.Str(child.id.replace('_', ' '))
        elif not isinstance(child, ast.Str):
            child = self.visit(child)
        new_args.append(child)

    return self.make_call(node, node.func.id, new_args, node.keywords)

def visit_Subscript(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_Subscript`` function.
    Make updates to handle the multiworld.
    """
    if isinstance(node.value, ast.Name):
        s = node.slice if isinstance(node.slice, ast.Name) else node.slice.value
        return ast.Subscript(
            value=ast.Attribute(
                ########################
                # Begin AP modified code
                value=ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Attribute(
                            value=ast.Name(id='state', ctx=ast.Load()),
                            attr='multiworld',
                            ctx=ast.Load()),
                        attr='worlds',
                        ctx=ast.Load()),
                    slice=ast.Index(value=ast.Constant(self.player)),
                    ctx=ast.Load()),
                # End AP modified code
                ########################
                attr=node.value.id,
                ctx=ast.Load()),
            slice=ast.Index(value=ast.Str(s.id.replace('_', ' '))),
            ctx=node.ctx)
    else:
        return node

def visit_BoolOp(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``visit_BoolOp`` function.
    Uses the ``player`` class attribute as an argument when running ``ast.Call``.
    Uses ``has_any`` and ``has_all`` instead of ``has_any_of`` and ``has_all_of``.
    """
    # Everything else must be visited, then can be removed/reduced to.
    early_return = isinstance(node.op, ast.Or)
    ########################
    # Begin AP modified code
    groupable = 'has_any' if early_return else 'has_all'
    # End AP modified code
    ########################
    items = set()
    new_values = []
    # if any elt is True(And)/False(Or), we can omit it
    # if any is False(And)/True(Or), the whole node can be replaced with it
    for elt in list(node.values):
        if isinstance(elt, ast.Str):
            items.add(elt.s)
        elif isinstance(elt, ast.Name) and elt.id in nonaliases:
            items.add(escaped_items[elt.id])
        else:
            # It's possible this returns a single item check,
            # but it's already wrapped in a Call.
            elt = self.visit(elt)
            if isinstance(elt, ast.NameConstant):
                if elt.value == early_return:
                    return elt
                # else omit it
            elif (isinstance(elt, ast.Call) and isinstance(elt.func, ast.Attribute)
                    and elt.func.attr in ('has', groupable) and len(elt.args) == 1):
                args = elt.args[0]
                if isinstance(args, ast.Str):
                    items.add(args.s)
                else:
                    items.update(it.s for it in args.elts)
            elif isinstance(elt, ast.BoolOp) and node.op.__class__ == elt.op.__class__:
                new_values.extend(elt.values)
            else:
                new_values.append(elt)

    # package up the remaining items and values
    if not items and not new_values:
        # all values were True(And)/False(Or)
        return ast.NameConstant(not early_return)

    if items:
        node.values = [ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='state', ctx=ast.Load()),
                ########################
                # Begin AP modified code
                attr='has_any' if early_return else 'has_all',
                ctx=ast.Load()),
            args=[ast.Tuple(elts=[ast.Str(i) for i in items], ctx=ast.Load()), ast.Constant(self.player)],
            # End AP modified code
            ########################
            keywords=[])] + new_values
    else:
        node.values = new_values
    if len(node.values) == 1:
        return node.values[0]
    return node

def make_call(self, node, name, args, keywords):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``make_call`` function.
    Uses the ``kwarg_defaults`` class attribute to add to ``keywords``.

    Generates an ast.Call invoking the given State function 'name',
    providing given args and keywords, and adding in additional
    keyword args from kwarg_defaults (age, etc.)
    """
    if not hasattr(State, name):
        raise Exception('Parse Error: No such function State.%s' % name, self.current_spot.name, ast.dump(node, False))

    ########################
    # Begin AP modified code
    for (k, v) in self.kwarg_defaults.items():
        keywords.append(ast.keyword(arg=f'{k}', value=ast.Constant(v)))
    # End AP modified code
    ########################

    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='state', ctx=ast.Load()),
            attr=name,
            ctx=ast.Load()),
        args=args,
        keywords=keywords)

def replace_subrule(self, target, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``replace_subrule`` function.
    Uses the ``player`` class attribute as an argument when running ``ast.Call``.
    """
    rule = ast.dump(node, False)
    if rule in self.replaced_rules[target]:
        return self.replaced_rules[target][rule]

    subrule_name = target + ' Subrule %d' % (1 + len(self.replaced_rules[target]))
    # Save the info to be made into a rule later
    self.delayed_rules.append((target, node, subrule_name))
    # Replace the call with a reference to that item
    item_rule = ast.Call(
        func=ast.Attribute(
            value=ast.Name(id='state', ctx=ast.Load()),
            attr='has',
            ctx=ast.Load()),
        ########################
        # Begin AP modified code
        args=[ast.Str(subrule_name), ast.Constant(self.player)],
        # End AP modified code
        ########################
        keywords=[])
    # Cache the subrule for any others in this region
    # (and reserve the item name in the process)
    self.replaced_rules[target][rule] = item_rule
    return item_rule

def create_delayed_rules(self):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``create_delayed_rules`` function.
    Uses ``multiworld`` to get the region. Uses AP's ``OOTLocation``. Uses the AP ``set_rule``
    function to add delayed rules.

    Requires the target regions have been defined in the world.
    """
    for region_name, node, subrule_name in self.delayed_rules:
        ########################
        # Begin AP modified code
        region = self.world.multiworld.get_region(region_name, self.player)
        event = OOTLocation(self.player, subrule_name, type='Event', parent=region, internal=True)
        event.show_in_spoiler = False
        # End AP modified code
        ########################

        self.current_spot = event
        # This could, in theory, create further subrules.
        access_rule = self.make_access_rule(self.visit(node))
        if access_rule is self.rule_cache.get('NameConstant(False)'):
            event.access_rule = None
            event.never = True
            logging.getLogger('').debug('Dropping unreachable delayed event: %s', event.name)
        else:
            if access_rule is self.rule_cache.get('NameConstant(True)'):
                event.always = True
            ########################
            # Begin AP modified code
            set_rule(event, access_rule)
            region.locations.append(event)

            self.world.make_event_item(subrule_name, event)
            # End AP modified code
            ########################
    # Safeguard in case this is called multiple times per world
    self.delayed_rules.clear()

def make_access_rule(self, body):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``make_access_rule`` function.
    Uses the ``kwarg_defaults`` class attribute.
    """
    rule_str = ast.dump(body, False)
    if rule_str not in self.rule_cache:
        # requires consistent iteration on dicts
        ########################
        # Begin AP modified code
        kwargs = [ast.arg(arg=k) for k in self.kwarg_defaults.keys()]
        kwd = list(map(ast.Constant, self.kwarg_defaults.values()))
        # End AP modified code
        ########################
        try:
            self.rule_cache[rule_str] = eval(compile(
                ast.fix_missing_locations(
                    ast.Expression(ast.Lambda(
                        args=ast.arguments(
                            posonlyargs=[],
                            args=[ast.arg(arg='state')],
                            defaults=[],
                            kwonlyargs=kwargs,
                            kw_defaults=kwd),
                        body=body))),
                '<string>', 'eval'),
                # globals/locals. if undefined, everything in the namespace *now* would be allowed
                allowed_globals)
        except TypeError as e:
            raise Exception('Parse Error: %s' % e, self.current_spot.name, ast.dump(body, False))
    return self.rule_cache[rule_str]

## Handlers for compile-time optimizations (former State functions)

def at_day(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``at_day`` function.
    Uses the AP ``CollectionState`` class to perform state checks.
    """
    if self.world.ensure_tod_access:
        # tod has DAY or (tod == NONE and (ss or find a path from a provider))
        # parsing is better than constructing this expression by hand
        ########################
        # Begin AP modified code
        r = self.current_spot if type(self.current_spot) == OOTRegion else self.current_spot.parent_region
        return ast.parse(f"(state.has('Ocarina', player) and state.has('Suns Song', player)) or state._oot_reach_at_time('{r.name}', TimeOfDay.DAY, [], player)", mode='eval').body
        # End AP modified code
        ########################
    return ast.NameConstant(True)

def at_dampe_time(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``at_dampe_time`` function.
    Uses the AP's ``CollectionState`` to perform state checks.
    """
    if self.world.ensure_tod_access:
        # tod has DAMPE or (tod == NONE and (find a path from a provider))
        # parsing is better than constructing this expression by hand
        ########################
        # Begin AP modified code
        r = self.current_spot if type(self.current_spot) == OOTRegion else self.current_spot.parent_region
        return ast.parse(f"state._oot_reach_at_time('{r.name}', TimeOfDay.DAMPE, [], player)", mode='eval').body
        # End AP modified code
        ########################
    return ast.NameConstant(True)

def at_night(self, node):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``at_night`` function.
    Uses the AP's ``CollectionState`` to perform state checks.
    """
    if self.current_spot.type == 'GS Token' and self.world.logic_no_night_tokens_without_suns_song:
        # Using visit here to resolve 'can_play' rule
        return self.visit(ast.parse('can_play(Suns_Song)', mode='eval').body)
    if self.world.ensure_tod_access:
        # tod has DAMPE or (tod == NONE and (ss or find a path from a provider))
        # parsing is better than constructing this expression by hand
        ########################
        # Begin AP modified code
        r = self.current_spot if type(self.current_spot) == OOTRegion else self.current_spot.parent_region
        return ast.parse(f"(state.has('Ocarina', player) and state.has('Suns Song', player)) or state._oot_reach_at_time('{r.name}', TimeOfDay.DAMPE, [], player)", mode='eval').body
        # End AP modified code
        ########################
    return ast.NameConstant(True)

def parse_spot_rule(self, spot):
    """
    Modified implementation of ``Rule_AST_Transformer``'s ``parse_spot_rule`` function.
    Uses the AP ``set_rule`` function to add spot rule.
    """
    rule = spot.rule_string.split('#', 1)[0].strip()

    access_rule = self.parse_rule(rule, spot)
    ########################
    # Begin AP modified code
    set_rule(spot, access_rule)
    # End AP modified code
    ########################
    if access_rule is self.rule_cache.get('NameConstant(False)'):
        spot.never = True
    elif access_rule is self.rule_cache.get('NameConstant(True)'):
        spot.always = True

# AP-specific Hijacking functions
def current_spot_child_access(self, node):
    r = self.current_spot if type(self.current_spot) == OOTRegion else self.current_spot.parent_region
    return ast.parse(f"state._oot_reach_as_age('{r.name}', 'child', {self.player})", mode='eval').body

def current_spot_adult_access(self, node):
    r = self.current_spot if type(self.current_spot) == OOTRegion else self.current_spot.parent_region
    return ast.parse(f"state._oot_reach_as_age('{r.name}', 'adult', {self.player})", mode='eval').body

def current_spot_starting_age_access(self, node):
    return self.current_spot_child_access(node) if self.world.starting_age == 'child' else self.current_spot_adult_access(node)

def has_bottle(self, node):
    return ast.parse(f"state._oot_has_bottle({self.player})", mode='eval').body

def can_live_dmg(self, node):
    return ast.parse(f"state._oot_can_live_dmg({self.player}, {node.args[0].value})", mode='eval').body

def region_has_shortcuts(self, node):
    return ast.parse(f"state._oot_region_has_shortcuts({self.player}, '{node.args[0].value}')", mode='eval').body

# Patch OoTR's Rule_AST_Transformer functions with our modified functions
Rule_AST_Transformer.__init__ = __init__
Rule_AST_Transformer.visit_Name = visit_Name
Rule_AST_Transformer.visit_Str = visit_Str
Rule_AST_Transformer.visit_Tuple = visit_Tuple
Rule_AST_Transformer.visit_Call = visit_Call
Rule_AST_Transformer.visit_Subscript = visit_Subscript
Rule_AST_Transformer.visit_BoolOp = visit_BoolOp
Rule_AST_Transformer.make_call = make_call
Rule_AST_Transformer.replace_subrule = replace_subrule
Rule_AST_Transformer.create_delayed_rules = create_delayed_rules
Rule_AST_Transformer.make_access_rule = make_access_rule
Rule_AST_Transformer.at_day = at_day
Rule_AST_Transformer.at_dampe_time = at_dampe_time
Rule_AST_Transformer.at_night = at_night
Rule_AST_Transformer.parse_spot_rule = parse_spot_rule
Rule_AST_Transformer.current_spot_child_access = current_spot_child_access
Rule_AST_Transformer.current_spot_adult_access = current_spot_adult_access
Rule_AST_Transformer.current_spot_starting_age_access = current_spot_starting_age_access
Rule_AST_Transformer.has_bottle = has_bottle
Rule_AST_Transformer.can_live_dmg = can_live_dmg
Rule_AST_Transformer.region_has_shortcuts = region_has_shortcuts

