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
    console.log("New question called!");
    var questions_node = document.getElementById("questions");
    var questions = getDirectChildNodes(questions_node);
    console.log("Questions");
    console.log(questions);

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

    // Create the new question div
    var new_question = document.createElement("div");
    new_question.setAttribute("id", new_question_label);

    // Build the CSRF div
    var csrf_div = document.createElement("div");
    csrf_div.setAttribute("style", "display:none;");
    csrf_div.appendChild(new_question_csrf_node);

    new_question.appendChild(csrf_div);

    // Build the question 'title'
    var question_p = document.createElement("p");
    question_p.appendChild(document.createTextNode("Question " + (new_question_id + 1) + ":"));

    new_question.appendChild(question_p);

    // Build the question 'question'
    var question_question_div = document.createElement("div");
    question_question_div.appendChild(document.createTextNode(new_question_label + "-question: "));

    var question_question_input = document.createElement("input");
    question_question_input.setAttribute("id", new_question_label + "-question");
    question_question_input.setAttribute("name", new_question_label + "-question");
    question_question_input.setAttribute("type", "text");
    question_question_input.setAttribute("value","");
    question_question_div.appendChild(question_question_input);

    new_question.appendChild(question_question_div);

    // Build the question 'type'
    var question_type_div = document.createElement("div");
    question_type_div.appendChild(document.createTextNode(new_question_label + "-question_type: "));

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
    new_question.appendChild(question_type_div);

    // Build the question 'type_max'
    var question_type_max_div = document.createElement("div");
    question_type_max_div.appendChild(document.createTextNode(new_question_label + "-question_type_max: "));

    var question_type_max_input = document.createElement("input");
    question_type_max_input.setAttribute("id", new_question_label + "-question_type_max");
    question_type_max_input.setAttribute("name", new_question_label + "-question-type_max");
    question_type_max_input.setAttribute("type", "text");
    question_type_max_input.setAttribute("value","");
    question_type_max_div.appendChild(question_type_max_input);

    new_question.appendChild(question_type_max_div);

    // Build the question 'choices'
    var question_choices_div = document.createElement("div");
    question_choices_div.setAttribute("id", new_question_label + "-choices");

    var question_choices_p = document.createElement("p");
    question_choices_p.appendChild(document.createTextNode("Choices (for Question " + (new_question_id + 1) + "):"));
    question_choices_div.appendChild(question_choices_p);

    var question_choices_0 = document.createElement("div");
    question_choices_0.setAttribute("id", new_question_label + "-choices-0");

    var question_choices_csrf_div = document.createElement("div");
    question_choices_csrf_div.setAttribute("style", "display:none;");
    question_choices_csrf_div.appendChild(new_choice_csrf_node);

    question_choices_0.appendChild(question_choices_csrf_div);

    var question_choices_input_div = document.createElement("div");
    question_choices_input_div.appendChild(document.createTextNode(new_question_label + "-choices-0-choice: "));

    var question_choices_input = document.createElement("input");
    question_choices_input.setAttribute("id", new_question_label + "-choices-0-choice");
    question_choices_input.setAttribute("name", new_question_label + "-choices-0-choice");
    question_choices_input.setAttribute("type", "text");
    question_choices_input.setAttribute("value", "");

    question_choices_input_div.appendChild(question_choices_input);
    question_choices_0.appendChild(question_choices_input_div);
    question_choices_div.appendChild(question_choices_0);
    new_question.appendChild(question_choices_div);

    var question_choices_add_button = document.createElement("button");
    question_choices_add_button.setAttribute("class", "btn");
    question_choices_add_button.setAttribute("type", "button");
    question_choices_add_button.setAttribute("onclick", "newChoice(this)");
    question_choices_add_button.appendChild(document.createTextNode("New Choice"));
    new_question.appendChild(question_choices_add_button);

    questions_node.appendChild(new_question);
}

/**
 * Adds a new choice into the question, expects certain IDs to exist and the page to be setup in a particular way
 */
function newChoice(node) {
    console.log("New choice called!");
    var question_node = node.parentNode;
    var choices_node = document.getElementById(question_node.id + "-choices");
    var choices = getDirectChildNodes(choices_node, "DIV");

    // TODO: Made this instead the last 'visible' question
    var new_choice_id = choices.length;
    var choice_label = question_node.id + '-choices-' + new_choice_id;

    // Create the new Choice CSRF node (keeping the same token, as it somehow accepts it)
    var new_choice_csrf_node = document.getElementById(question_node.id + '-choices-0-csrf_token').cloneNode(true);
    new_choice_csrf_node.id = question_node.id + '-choices-' + new_choice_id + '-csrf_token';
    new_choice_csrf_node.name = question_node.id + '-choices-' + new_choice_id + '-csrf_token';

    var new_choice_div = document.createElement("div");
    new_choice_div.setAttribute("id", choice_label);

    // Build the CSRF div
    var choice_csrf_div = document.createElement("div");
    choice_csrf_div.setAttribute("style", "display:none;");
    choice_csrf_div.appendChild(new_choice_csrf_node);
    new_choice_div.appendChild(choice_csrf_div);

    // Build the choice 'choice'
    var choice_input_div = document.createElement("div");
    choice_input_div.appendChild(document.createTextNode(choice_label + "-choice: "));

    var choice_input = document.createElement("input");
    choice_input.setAttribute("id", choice_label + "-choice");
    choice_input.setAttribute("name", choice_label + "-choice");
    choice_input.setAttribute("type", "text");
    choice_input.setAttribute("value", "");
    choice_input_div.appendChild(choice_input);

    // Build the (optional) remove choice button
    if (new_choice_id > 0) {
        console.log("Creating remove button");
        var choice_remove = document.createElement("button");
        choice_remove.setAttribute("class", "btn");
        choice_remove.setAttribute("type", "button");
        choice_remove.setAttribute("onclick", "deleteNode(this.parentNode.parentNode)");
        choice_remove.appendChild(document.createTextNode("Remove Choice"));
        choice_input_div.appendChild(document.createTextNode(" <- "));
        choice_input_div.appendChild(choice_remove);
    }

    new_choice_div.appendChild(choice_input_div);
    choices_node.appendChild(new_choice_div);
}

/**
 * Take a reference to an element, and delete that element (including the passed in element)
 * @param node
 */
function deleteNode(node) {
    node.remove();
}
