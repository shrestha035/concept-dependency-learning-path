"""Adaptive live quiz and personalized learning path — owner: Shrestha."""

import streamlit as st
from common import concept_names, load, page_header
from cdlp.learning_path import api

page_header('My Learning Path', 'Shrestha', 'learning_path.json')

graph = load('validated_graph.json')
quiz = load('quiz_items.json')

names = {n['id']: n['name'] for n in graph['nodes']}

# Select learning target
target = st.selectbox(
    'What do you want to learn?',
    list(names),
    format_func=lambda c: names[c]
)

# Student confidence
self_report = st.slider(
    'How confident are you in this subject?',
    0, 100, 50, 10
)

# Quiz question limit
budget = st.slider(
    'Maximum quiz questions',
    1, 15, 5
)

key = (target, self_report)

# Initialize student state
if st.session_state.get('lp_key') != key:
    st.session_state.lp_key = key
    st.session_state.lp_mastery = {
        c: max(0.05, min(0.95, self_report / 100))
        for c in api.prerequisite_order(graph, target)
    }
    st.session_state.lp_answers = []
    st.session_state.lp_finished = False

# Restart diagnosis
if st.button('Restart diagnosis'):
    st.session_state.lp_mastery = {
        c: max(0.05, min(0.95, self_report / 100))
        for c in api.prerequisite_order(graph, target)
    }
    st.session_state.lp_answers = []
    st.session_state.lp_finished = False
    st.rerun()

asked = st.session_state.lp_answers

# Quiz progress
st.progress(
    min(len(asked) / budget, 1.0),
    text=f'{len(asked)} of {budget} questions'
)

# Select next adaptive question
question = (
    None
    if st.session_state.lp_finished or len(asked) >= budget
    else api.next_question(
        graph,
        quiz,
        {
            **st.session_state.lp_mastery,
            '__asked__': [a['item_id'] for a in asked]
        },
        target
    )
)

if question:

    st.subheader(
        f"Question: {names.get(question['concept_id'], question['concept_id'])}"
    )

    # Quiz form
    with st.form(key='quiz_' + question['id']):

        st.write(question['question'])

        choice = st.radio(
            'Choose an answer',
            question['options'],
            index=None
        )

        # FIX: Submit button must be inside the form
        submitted = st.form_submit_button(
            'Submit answer',
            use_container_width=True
        )

    # Process answer
    if submitted:

        if choice is None:
            st.warning('Please select an answer before submitting.')

        else:
            correct = choice == question['answer']

            st.session_state.lp_mastery = api.update_mastery(
                graph,
                st.session_state.lp_mastery,
                question['concept_id'],
                correct
            )

            asked.append({
                'item_id': question['id'],
                'correct': correct
            })

            st.rerun()

    # Finish quiz early
    if st.button('Finish quiz and see my path'):
        st.session_state.lp_finished = True
        st.rerun()

else:

    st.success(
        'Diagnosis complete. Here is your personalized path.'
    )

    # Generate personalized learning path
    steps = api.personalized_path(
        graph,
        st.session_state.lp_mastery,
        target
    )

    if not steps:
        st.success(
            'All concepts on this path are estimated mastered!'
        )

    # Display learning steps
    for index, step in enumerate(steps, 1):

        with st.expander(
            f"{index}. {names.get(step['concept_id'], step['concept_id'])}",
            expanded=True
        ):

            st.write(step['why'])

            for ev in step.get('evidence', []):
                st.caption(
                    f"Source: {ev['doc']}, page {ev['page']}"
                )

    # Mastery visualization
    st.subheader('Estimated mastery')

    st.bar_chart({
        names.get(c, c): p
        for c, p in st.session_state.lp_mastery.items()
    })

    st.caption(
        'Quiz-based mastery is an estimate, '
        'not a validated assessment of student competence.'
    )