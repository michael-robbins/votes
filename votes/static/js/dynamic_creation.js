/**
 * Takes a node and an optional tag to filter down to, and returns all *direct* children nodes
 * @param parent
 * @param filterTag
 * @returns {Array}
 */
function getDirectChildNodes(parent, filterTag) {
    var directChildren = [];

    // Filter down the child elements to a specific tag name
    filterTag = typeof filterTag !== 'undefined' ? filterTag : '';

    var children = parent.childNodes;

    for (var i=0; i < children.length; i++) {
        if (children[i].parentNode == parent && children[i].nodeType == 1) {
            if (filterTag != '') {
                // If we have a filter tag defined, then only push if it matches
                if (children[i].tagName == filterTag) {
                    directChildren.push(children[i]);
                }
            } else {
                directChildren.push(children[i]);
            }
        }
    }

    return directChildren;
}

// Inspiration for the below, credit where credit is due.
// http://stackoverflow.com/questions/11759769/howto-dynamically-generate-csrf-token-in-wtforms-with-flask

/**
 * Adds a new question onto the page, expects certain IDs to exist and the page to be setup in a particular way
 */
function newQuestion() {
    //console.log("New question called!");
    var questions_node = document.getElementById("questions");
    var questions = getDirectChildNodes(questions_node);
    //console.log("Questions");
    //console.log(questions);

    // TODO: Made this instead the last 'visible' question
    var new_question_id = questions.length;
    var new_question_label = 'questions-' + new_question_id;

    // Create the new Question CSRF node (keeping the same token, as it somehow accepts it)
    var new_question_csrf_node = document.getElementById("questions-0-csrf_token").cloneNode(true);
    new_question_csrf_node.id = new_question_label + '-csrf_token';
    new_question_csrf_node.name = new_question_label + '-csrf_token';

    // Create the new Choice CSRF node (keeping the same token, as it somehow accepts it)
    var new_choice_csrf_node = document.getElementById('questions-0-choices-0-csrf_token').cloneNode(true);
    new_choice_csrf_node.id = new_question_label + '-choices-0-csrf_token';
    new_choice_csrf_node.name = new_question_label + '-choices-0-csrf_token';

    // Create the new question div panel
    var new_question = document.createElement("div");
    new_question.setAttribute("class", "panel panel-primary");
    new_question.setAttribute("id", new_question_label);

    // Build the question div panel heading
    var panel_header = document.createElement("div");
    panel_header.setAttribute("class", "panel-heading");

    var panel_header_content = document.createElement("h3");
    panel_header_content.setAttribute("class", "panel-title");
    panel_header_content.appendChild(document.createTextNode("Question " + (new_question_id + 1)));
    panel_header.appendChild(panel_header_content);
    new_question.appendChild(panel_header);

    // Build the question div panel body
    var panel_body = document.createElement("div");
    panel_body.setAttribute("class", "panel-body");

    // Build the CSRF div
    var csrf_div = document.createElement("div");
    csrf_div.setAttribute("style", "display:none;");
    csrf_div.appendChild(new_question_csrf_node);
    panel_body.appendChild(csrf_div);

    // Build the hidden ID input
    var question_hidden_id = document.createElement("input");
    question_hidden_id.setAttribute("type", "hidden");
    question_hidden_id.setAttribute("id", "question-id");
    question_hidden_id.setAttribute("value", String(new_question_id));
    panel_body.appendChild(question_hidden_id);

    // Build the Question 'question' text entry
    var question_question_div = document.createElement("div");

    var question_question_label = document.createElement("label");
    question_question_label.setAttribute("for", new_question_label + "-question");
    question_question_label.appendChild(document.createTextNode("Question: "));
    question_question_div.appendChild(question_question_label);

    var question_question_input = document.createElement("input");
    question_question_input.setAttribute("id", new_question_label + "-question");
    question_question_input.setAttribute("name", new_question_label + "-question");
    question_question_input.setAttribute("type", "text");
    question_question_input.setAttribute("value","");
    question_question_div.appendChild(question_question_input);
    panel_body.appendChild(question_question_div);

    // Build the Question 'type' select entry
    var question_type_div = document.createElement("div");

    var question_type_label = document.createElement("label");
    question_type_label.setAttribute("for", new_question_label + "-question_type");
    question_type_label.appendChild(document.createTextNode("Question Type: "));
    question_type_div.appendChild(question_type_label);

    var question_type_select = document.createElement("select");
    question_type_select.setAttribute("id", new_question_label + "-question_type");
    question_type_select.setAttribute("name", new_question_label + "-question_type");

    var singlechoice_option = document.createElement("option");
    singlechoice_option.setAttribute("value", "SingleChoice");
    singlechoice_option.appendChild(document.createTextNode("Single Choice"));
    question_type_select.appendChild(singlechoice_option);

    var multiplechoice_option = document.createElement("option");
    multiplechoice_option.setAttribute("value", "MultipleChoice");
    multiplechoice_option.appendChild(document.createTextNode("Multiple Choice"));
    question_type_select.appendChild(multiplechoice_option);

    var freetext_option = document.createElement("option");
    freetext_option.setAttribute("value", "FreeText");
    freetext_option.appendChild(document.createTextNode("Free Text Field"));
    question_type_select.appendChild(freetext_option);

    var ranked_option = document.createElement("option");
    ranked_option.setAttribute("value", "Ranked");
    ranked_option.appendChild(document.createTextNode("Ranked Choices"));
    question_type_select.appendChild(ranked_option);

    question_type_div.appendChild(question_type_select);
    panel_body.appendChild(question_type_div);

    // Build the question 'type_max' number entry
    var question_type_max_div = document.createElement("div");

    var question_type_max_label = document.createElement("label");
    question_type_max_label.setAttribute("for", new_question_label + "-question_type_max");
    question_type_max_label.appendChild(document.createTextNode("Maximum entries for a choice: "));
    question_type_max_div.appendChild(question_type_max_label);

    var question_type_max_input = document.createElement("input");
    question_type_max_input.setAttribute("id", new_question_label + "-question_type_max");
    question_type_max_input.setAttribute("name", new_question_label + "-question-type_max");
    question_type_max_input.setAttribute("type", "text");
    question_type_max_input.setAttribute("value","");
    question_type_max_div.appendChild(question_type_max_input);
    panel_body.appendChild(question_type_max_div);
    panel_body.appendChild(document.createElement("br"));

    // Build the question 'choices', we can't use the function below, as there isn't an initial one to steal
    // This is another panel we are creating
    var question_choices_div = document.createElement("div");
    question_choices_div.setAttribute("class", "panel panel-success");
    question_choices_div.setAttribute("id", new_question_label + "-choices");

    // Create the panel header
    var question_choices_panel_header = document.createElement("div");
    question_choices_panel_header.setAttribute("class", "panel-heading");
    question_choices_panel_header.appendChild(document.createTextNode("Choices (for Question " + (new_question_id + 1) + ")"));
    question_choices_div.appendChild(question_choices_panel_header);

    // Create the unsorted list for the panel
    var choices_ul = document.createElement("ul");
    choices_ul.setAttribute("class", "list-group");

    // Create the first and only list item
    var choices_li = document.createElement("li");
    choices_li.setAttribute("class", "list-group-item");
    choices_li.setAttribute("id", new_question_label + "choices-0");

    // Create the CSRF token element for the li
    var choices_csrf_div = document.createElement("div");
    choices_csrf_div.setAttribute("style", "display:none;");
    choices_csrf_div.appendChild(new_choice_csrf_node);
    choices_li.appendChild(choices_csrf_div);

    // Create the text input
    var choices_input_div = document.createElement("div");
    choices_input_div.appendChild(document.createTextNode("Choice 1: "));

    var choices_input = document.createElement("input");
    choices_input.setAttribute("id", new_question_label + "-choices-0-choice");
    choices_input.setAttribute("name", new_question_label + "-choices-0-choice");
    choices_input.setAttribute("type", "text");
    choices_input.setAttribute("value", "");

    choices_input_div.appendChild(choices_input);
    choices_li.appendChild(choices_input_div);
    choices_ul.appendChild(choices_li);
    question_choices_div.appendChild(choices_ul);
    panel_body.appendChild(question_choices_div);

    var question_choices_add_button = document.createElement("button");
    question_choices_add_button.setAttribute("class", "btn btn-default");
    question_choices_add_button.setAttribute("type", "button");
    question_choices_add_button.setAttribute("onclick", "newChoice(this)");
    question_choices_add_button.appendChild(document.createTextNode("New Choice"));
    panel_body.appendChild(question_choices_add_button);
    new_question.appendChild(panel_body);
    questions_node.appendChild(new_question);
}

/**
 * Adds a new choice into the question, expects certain IDs to exist and the page to be setup in a particular way
 */
function newChoice(node) {
    //console.log("New choice called!");
    var question_node = node.parentNode.parentNode;
    var choices_node = document.getElementById(question_node.id + "-choices");

    var choices = getDirectChildNodes(choices_node, "UL")[0];
    //console.log(choices);

    // TODO: Made this instead the last 'visible' question
    var new_choice_id = choices.children.length;
    var choice_label = question_node.id + '-choices-' + new_choice_id;

    // Build the panel
    var new_choice_li = document.createElement("li");
    new_choice_li.setAttribute("class", "list-group-item");
    new_choice_li.setAttribute("id", choice_label);

    // Create the new Choice CSRF node (keeping the same token, as it somehow accepts it)
    var new_choice_csrf_node = document.getElementById(question_node.id + '-choices-0-csrf_token').cloneNode(true);
    new_choice_csrf_node.id = question_node.id + '-choices-' + new_choice_id + '-csrf_token';
    new_choice_csrf_node.name = question_node.id + '-choices-' + new_choice_id + '-csrf_token';

    // Build the CSRF div
    var choice_csrf_div = document.createElement("div");
    choice_csrf_div.setAttribute("style", "display:none;");
    choice_csrf_div.appendChild(new_choice_csrf_node);
    new_choice_li.appendChild(choice_csrf_div);

    // Create the actual label & input field
    var choice_input_div = document.createElement("div");
    choice_input_div.appendChild(document.createTextNode("Choice " + (new_choice_id + 1) + ": "));

    var choice_input = document.createElement("input");
    choice_input.setAttribute("id", choice_label + "-choice");
    choice_input.setAttribute("name", choice_label + "-choice");
    choice_input.setAttribute("type", "text");
    choice_input.setAttribute("value", "");
    choice_input_div.appendChild(choice_input);

    // Build the (optional) remove choice button
    if (new_choice_id > 0) {
        var choice_remove = document.createElement("button");
        choice_remove.setAttribute("class", "btn btn-warning");
        choice_remove.setAttribute("type", "button");
        choice_remove.setAttribute("onclick", "deleteNode(this.parentNode.parentNode)");
        choice_remove.appendChild(document.createTextNode("Remove Choice"));

        var icon_span = document.createElement("span");
        icon_span.setAttribute("class", "glyphicon glyphicon-arrow-left");
        icon_span.setAttribute("aria-hidden", "true");

        // Buzz to Woody "Space hacks, space hacks everywhere"
        choice_input_div.appendChild(document.createTextNode(" "));
        choice_input_div.appendChild(icon_span);
        choice_input_div.appendChild(document.createTextNode(" "));
        choice_input_div.appendChild(choice_remove);
    }

    new_choice_li.appendChild(choice_input_div);
    choices.appendChild(new_choice_li);
}

/**
 * Take a reference to an element, and delete that element (including the passed in element)
 * @param node
 */
function deleteNode(node) {
    node.remove();
}
