// Overwritten PFDL rules
program_statement:
	rule_ | orderStep;

struct_id: (LOCATION | EVENT | TIME | STARTS_WITH_UPPER_C_STR);

taskStatement: eventStatement | constraintStatement;

statement:
	transportStatement
	| moveStatement
	| actionStatement;

primitive:
	LOCATION
	| EVENT
	| TIME;

expression:
	attribute_access
	| rule_call;

// {Plugin_Move_To_Front}
attribute_access:
	STARTS_WITH_LOWER_C_STR;

// MF-Plugin exclusive
transportStatement:
	TRANSPORT NL FROM tosCollectionStatement TO tosCollectionStatement;

tosCollectionStatement:
	STARTS_WITH_LOWER_C_STR (COMMA STARTS_WITH_LOWER_C_STR)* NL;

moveStatement: MOVE NL TO STARTS_WITH_LOWER_C_STR NL;

actionStatement: ACTION NL DO STARTS_WITH_LOWER_C_STR NL;

constraintStatement: CONSTRAINTS (expression | json_object) NL;

moveOrderStep:
	MOVE_ORDER_STEP STARTS_WITH_LOWER_C_STR INDENT mosStatement+ DEDENT END;

mosStatement:
	locationStatement
	| eventStatement
	| onDoneStatement;

actionOrderStep:
	ACTION_ORDER_STEP STARTS_WITH_LOWER_C_STR INDENT aosStatement+ DEDENT END;

aosStatement:
	parameterStatement
	| eventStatement
	| onDoneStatement;

orderStep: transportOrderStep | moveOrderStep | actionOrderStep;

transportOrderStep:
	TRANSPORT_ORDER_STEP STARTS_WITH_LOWER_C_STR INDENT tosStatement+ DEDENT END;

tosStatement:
	locationStatement
	| parameterStatement
	| eventStatement
	| onDoneStatement;

locationStatement: LOCATION STARTS_WITH_LOWER_C_STR NL;

parameterStatement: PARAMETERS (value | json_object) NL;

eventStatement:
	STARTED_BY expression NL
	| FINISHED_BY expression NL;

onDoneStatement: ON_DONE STARTS_WITH_LOWER_C_STR NL;

rule_: RULE rule_call INDENT (expression NL)+ DEDENT END;

rule_call:
	STARTS_WITH_LOWER_C_STR LEFT_PARENTHESIS (
		rule_parameter (COMMA rule_parameter)*
	)? RIGHT_PARENTHESIS;

rule_parameter:
	(STARTS_WITH_LOWER_C_STR | value) (ASSIGNMENT value)?;