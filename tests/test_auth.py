def register(client, email='new@usiu.ac.ke', password='secret123'):
    return client.post('/register', data={
        'full_name': 'New Student', 'email': email,
        'reg_no': '654321', 'password': password,
    })


def test_student_can_register_and_log_in(client):
    assert register(client).status_code == 302
    response = client.post('/login', data={
        'email': 'new@usiu.ac.ke', 'password': 'secret123'})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['role'] == 'student'


def test_wrong_password_is_rejected(client):
    register(client)
    response = client.post('/login', data={
        'email': 'new@usiu.ac.ke', 'password': 'wrong'})
    assert b'Incorrect email or password' in response.data


def test_duplicate_email_is_rejected(client):
    register(client)
    response = register(client)
    assert b'already registered' in response.data


def test_logout_clears_session(client, make_user, login_as):
    user_id, _ = make_user('student')
    login_as(user_id, 'student')
    client.get('/logout')
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_home_redirects_to_login_when_logged_out(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')


def test_login_page_offers_student_and_lecturer(client):
    response = client.get('/login')
    assert b'value="student"' in response.data
    assert b'value="lecturer"' in response.data


def test_lecturer_can_log_in_as_lecturer(client, make_user):
    _, email = make_user('lecturer')
    response = client.post('/login', data={
        'email': email, 'password': 'secret123', 'role': 'lecturer'})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['role'] == 'lecturer'


def test_lecturer_lands_on_lecturer_page(client, make_user):
    _, email = make_user('lecturer')
    response = client.post('/login', data={
        'email': email, 'password': 'secret123', 'role': 'lecturer'},
        follow_redirects=True)
    assert response.request.path == '/lecturer/assignments'


def test_lecturer_account_rejected_on_student_login(client, make_user):
    _, email = make_user('lecturer')
    response = client.post('/login', data={
        'email': email, 'password': 'secret123', 'role': 'student'})
    assert b'not a student account' in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_student_account_rejected_on_lecturer_login(client, make_user):
    _, email = make_user('student')
    response = client.post('/login', data={
        'email': email, 'password': 'secret123', 'role': 'lecturer'})
    assert b'not a lecturer account' in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_student_can_log_in_as_student(client, make_user):
    _, email = make_user('student')
    response = client.post('/login', data={
        'email': email, 'password': 'secret123', 'role': 'student'})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['role'] == 'student'