"""
This module implements a basic Object Relational Mapping (ORM) for managing user data using repository pattern.
It provides classes and methods for creating, retrieving, updating, and deleting user records
in a SQLite database.

Note: 
Classes like Entity, User, RepoMapper, UserRepoMapper, Repository, and test classes
are better placed in others modules and packages for clearer project organization.
For better code review, I moved them into a single file for better reviewing
"""

import re
from ipaddress import ip_address
from abc import ABC, abstractmethod
import sqlite3
from typing import List, Optional
import unittest
from unittest import mock


class Entity:
    """
    Represents a base entity class with a unique identifier (UUID).
    Other objects (any objects we would like to map from or to related tables in the database) should inherit this class.

    Attributes:
        entity_uuid (str): The unique identifier (UUID) of the entity.
    """

    def __init__(self, entity_uuid: str) -> None:
        """
        Initialize the Entity class with a unique identifier (UUID).

        Parameters:
            entity_uuid (str): The unique identifier (UUID) of the entity.

        Returns:
            None
        """
        self.entity_uuid = entity_uuid

    @property
    def entity_uuid(self):
        """get uuid"""
        return self.__entity_uuid

    @entity_uuid.setter
    def entity_uuid(self, entity_uuid):
        """set uuid"""
        self.__entity_uuid = entity_uuid


class User(Entity):
    """
    Represents a user entity with his/her information.

    User information: uuid, name, email, last login ip, user type.
    """

    def __init__(self, user_uuid: str, user_name: str, email: str, last_login_ip: str, user_type: int) -> None:
        """
        constructor of User entity

        Parameters:
        user_uuid (str): The unique identifier (UUID) of the user.
        user name (str): The user's name.
        email (str): The user's email address.
        last_login_ip (str): The user's last login IP address (should be valid IPv4 or IPv6) - It can be used to check abnormal log-in.
        user_type (int): The user's type (e.g., admin - type 3, premium user - type 2, regular user - type 1).
        """
        super().__init__(user_uuid)
        self.user_name = user_name
        self.email = email
        self.last_login_ip = last_login_ip
        self.user_type = user_type

    @property
    def user_name(self):
        """get user name"""
        return self.__user_name

    @user_name.setter
    def user_name(self, value):
        """set user name"""
        self.__user_name = value

    @property
    def email(self):
        """get email"""
        return self.__email

    @email.setter
    def email(self, value):
        """validate and set email"""
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise ValueError("Invalid email format")
        self.__email = value

    @property
    def last_login_ip(self):
        """get user last login ip address"""
        return self.__last_login_ip

    @last_login_ip.setter
    def last_login_ip(self, value):
        """validate and set user last login ip address"""
        # ip_address check ip validity
        ip_address(value)
        self.__last_login_ip = value

    @property
    def user_type(self):
        """get user type"""
        return self.__user_type

    @user_type.setter
    def user_type(self, value):
        """validate and set user type"""
        if value < 1 or value > 3:
            raise ValueError("Invalid user type")
        self.__user_type = value


class RepoMapper(ABC):
    """
    Represents an abstract class for mapping between Entity objects and their corresponding
    dictionary representation in the repository. This class should be inherited by specific
    mapper classes for each entity type.

    Methods:
        map_from_repo(self, record: sqlite3.Row) -> Entity: An abstract method that should be
            implemented by the inheriting class to map a record from the repository to an Entity object.
            The keys in record should have same names as related columns in the database.
        map_to_repo(self, entity: Entity) -> dict: An abstract method that should be
            implemented by the inheriting class to map an Entity object to a dictionary representation
            for the repository. The dictionary should have same names as related columns in the database.
    """

    @abstractmethod
    def map_from_repo(self, record: sqlite3.Row) -> Entity:
        """
        Map a record from the repository to an Entity object.

        Parameters:
            record (sqlite3.Row): A record from the repository. 
                The keys in record should have same names as related columns in the database.

        Returns:
            Entity: An Entity object representing the record.
        """

    @abstractmethod
    def map_to_repo(self, entity: Entity) -> dict:
        """
        Map an Entity object to a dictionary representation for the repository.

        Parameters:
            entity (Entity): An Entity object to be mapped to a dictionary representation.

        Returns:
            dict: A dictionary representation of the Entity object for the repository. 
            The dictionary should have same names as related columns in the database.
        """


class UserRepoMapper(RepoMapper):
    """
    Represents a UserRepoMapper class for mapping between User objects and their corresponding
    dictionary representation in the repository. This class inherits from the RepoMapper class.

    Methods:
        map_from_repo(self, record: sqlite3.Row) -> User: 
            Maps a record from the repository to a User object.
            The keys in record should have same names as related columns in the user database.
        map_to_repo(self, entity: User) -> dict: 
            Maps a User object to a dictionary representation
            for the repository. The dictionary should have same keys as related columns in the user database.
    """

    def map_from_repo(self, record: sqlite3.Row) -> User:
        """
        Map a record from the repository to a User object.

        Parameters:
            record (sqlite3.Row): A record from the repository. 
            The keys in record should have same names as related columns in the user database.

        Returns:
            User: A User object representing the record.
        """
        return User(record['uuid'],
                    record['user_name'],
                    record['email'],
                    record['last_login_ip'],
                    record['user_type']
                    )

    def map_to_repo(self, entity: User) -> dict:
        """
        Map a User object to a dictionary representation for the repository.

        Parameters:
            entity (User): A User object to be mapped to a dictionary representation.

        Returns:
            dict: A dictionary representation of the User object for the repository. The dictionary should have same keys as related columns in the user database.
        """
        user_data = {
            'uuid': entity.entity_uuid,
            'user_name': entity.user_name,
            'email': entity.email,
            'last_login_ip': entity.last_login_ip,
            'user_type': entity.user_type,
        }

        return user_data


class Repository:
    """
    Represents a Repository class for managing Entity objects in a SQLite database.
    This class provides methods for creating, retrieving, updating, and deleting Entity records
    in the database, and it calls mapper to map retrieved data to Entity object. 
    It should be inherited by specific repository classes for each entity type.

    Attributes:
        table_name (str): The name of the table in the SQLite database where the Entity records are stored.
        repo_mapper (RepoMapper): The mapper that maps between database data and Entity object.

    Methods:
        create_connection(self) -> sqlite3.Connection: 
            Creates a connection to the SQLite database.
        fetch_all(self, include_deleted=False) -> List[Entity]: 
            Fetches all records from the database and returns them as a list of Entity objects.
        fetch_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]: 
            Fetches a single record from the database by its UUID and returns it as an Entity object.
        add_one(self, entity: Entity) -> Optional[Entity]: 
            Adds a new Entity record to the database and returns the added Entity object.
        soft_delete_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]: 
            Soft deletes a record from the database by its UUID and returns the deleted Entity object.
        delete_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]: 
            Deletes a record from the database by its UUID and returns the deleted Entity object.
        update_one(self, entity: Entity) -> Optional[Entity]: 
            Updates a record in the database with the provided Entity object and returns the updated Entity object.
    """

    def __init__(self, repo_table_name: str, repo_mapper: RepoMapper) -> None:
        """
        Initialize the Repository class with a table name and a mapper.

        Parameters:
            repo_table_name (str): The name of the table in the SQLite database where the Entity records are stored.
            repo_mapper (RepoMapper): The mapper that maps between dictionary and Entity object.

        Returns:
            None
        """
        self.table_name = repo_table_name
        self.repo_mapper = repo_mapper

    @property
    def table_name(self) -> str:
        """get table name"""
        return self.__table_name

    @table_name.setter
    def table_name(self, value: str) -> None:
        """set table name"""
        self.__table_name = value

    @property
    def repo_mapper(self) -> RepoMapper:
        """get repo mapper"""
        return self.__repo_mapper

    @repo_mapper.setter
    def repo_mapper(self, value: RepoMapper) -> None:
        """set repo mapper"""
        self.__repo_mapper = value

    def create_connection(self):
        """
        Creates a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object to the SQLite database.
        """
        conn = None
        conn = sqlite3.connect('demo.db')
        return conn

    def fetch_all(self, include_deleted=False) -> List[Entity]:
        """
        Fetches all records from the database and returns them as a list of Entity objects.

        Parameters:
            include_deleted (bool): If True, includes records marked as deleted in the returned list. False otherwise. False default.

        Returns:
            List[Entity]: A list of Entity objects representing the records in the database.
        """
        query = f"SELECT * FROM {self.table_name}" if include_deleted else f"SELECT * FROM {self.table_name} WHERE deleted = 0"
        conn = self.create_connection()
        conn.row_factory = sqlite3.Row
        cr = conn.cursor()
        cr.execute(query)
        fetched_data = cr.fetchall()
        conn.close()
        return [self.repo_mapper.map_from_repo(row) for row in fetched_data]

    def fetch_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]:
        """
        Fetches a single record from the database by its UUID and returns it as an Entity object.

        Parameters:
            entity_uuid (str): The unique identifier (UUID) of the entity to be fetched.

        Returns:
            Optional[Entity]: An Entity object representing the fetched record, or None if the record is not found.
        """
        query = f"SELECT * FROM {self.table_name} WHERE uuid = '{entity_uuid}'"
        conn = self.create_connection()
        conn.row_factory = sqlite3.Row
        cr = conn.cursor()
        cr.execute(query)
        fetched_one_record = cr.fetchone()
        conn.close()
        return None if not fetched_one_record else self.repo_mapper.map_from_repo(fetched_one_record)

    def add_one(self, entity: Entity) -> Optional[Entity]:
        """
        Adds a new Entity record to the database and returns the added Entity object.

        Parameters:
            entity (Entity): The Entity object to be added to the database.

        Returns:
            Optional[Entity]: The added Entity object, or None if the operation fails.
        """
        entity_data = self.repo_mapper.map_to_repo(entity)
        keys = entity_data.keys()
        columns = ', '.join(keys)
        placeholders = ', '.join('?' * len(entity_data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        conn = self.create_connection()
        cr = conn.cursor()
        cr.execute(query, tuple(entity_data[k] for k in keys))
        conn.commit()
        conn.close()
        return self.fetch_one_by_uuid(entity.entity_uuid)

    def soft_delete_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]:
        """
        Soft deletes a record from the database by its UUID and returns the deleted Entity object.

        Parameters:
            entity_uuid (str): The unique identifier (UUID) of the entity to be soft deleted.

        Returns:
            Optional[Entity]: The soft deleted Entity object, or None if the operation fails.
        """
        restored_entity_for_soft_delete = self.fetch_one_by_uuid(entity_uuid)
        if restored_entity_for_soft_delete:
            query = f"UPDATE {self.table_name} SET deleted = 1 WHERE uuid = '{entity_uuid}'"
            conn = self.create_connection()
            cr = conn.cursor()
            cr.execute(query)
            conn.commit()
            conn.close()
        return restored_entity_for_soft_delete

    def delete_one_by_uuid(self, entity_uuid: str) -> Optional[Entity]:
        """
        Deletes a record from the database by its UUID and returns the deleted Entity object.

        Parameters:
            entity_uuid (str): The unique identifier (UUID) of the entity to be deleted.

        Returns:
            Optional[Entity]: The deleted Entity object, or None if the operation fails.
        """
        restored_entity_for_delete = self.fetch_one_by_uuid(entity_uuid)
        if restored_entity_for_delete:
            query = f"DELETE FROM {self.table_name} Where uuid = '{entity_uuid}'"
            conn = self.create_connection()
            cr = conn.cursor()
            cr.execute(query)
            conn.commit()
            conn.close()
        return restored_entity_for_delete

    def update_one(self, entity: Entity) -> Optional[Entity]:
        """
        Updates a record in the database with the provided Entity object and returns the updated Entity object.

        Parameters:
            entity (Entity): The Entity object with updated information to be updated in the database.

        Returns:
            Optional[Entity]: The updated Entity object, or None if the operation fails.
        """
        entity_data = self.repo_mapper.map_to_repo(entity)
        keys = [k for k in entity_data.keys() if k != 'uuid']
        set_values = ', '.join(
            [f"{key} = ?" for key in keys])
        query = f"UPDATE {self.table_name} SET {set_values} WHERE uuid = '{entity.entity_uuid}'"
        conn = self.create_connection()
        cr = conn.cursor()
        cr.execute(
            query, (tuple(entity_data[k] for k in keys)))
        conn.commit()
        conn.close()
        return self.fetch_one_by_uuid(entity.entity_uuid)


class UserRepository(Repository):
    """
    Represents a UserRepository class for managing User objects in a SQLite database.
    This class inherits from the Repository class and provides additional methods specific to User entities.

    Methods:
        fetch_users_by_user_type(self, user_type: int) -> List[User]: 
            Fetches all User records with the specified user type from the database and returns them as a list of User objects.
    """

    def __init__(self) -> None:
        """
        Initialize the UserRepository class.

        Returns:
            None
        """
        super().__init__('user', UserRepoMapper())

    def fetch_users_by_user_type(self, user_type: int) -> List[User]:
        """
        Fetches all User records with the specified user type from the database and returns them as a list of User objects.

        Parameters:
            user_type (int): The user type to filter User records by.

        Returns:
            List[User]: A list of User objects with the specified user type.
        """
        query = f"SELECT * FROM {self.table_name} WHERE user_type = '{user_type}'"
        conn = self.create_connection()
        conn.row_factory = sqlite3.Row
        cr = conn.cursor()
        cr.execute(query)
        fetched_data = cr.fetchall()
        conn.close()
        return [self.repo_mapper.map_from_repo(row) for row in fetched_data]


# Below are classes for unit testing

class TestUserSetters(unittest.TestCase):
    """
    This class test the setters in User class.
    This class inherits from the unittest.
    """

    def setUp(self):
        """set up a user object for testing"""
        self.user = User('test-uuid', 'John Doe',
                         'john.doe@qt.com', '192.168.1.1', 1)

    def test_set_user_name(self):
        """Test setting a new user name."""
        self.user.user_name = 'Jerry'
        self.assertEqual(self.user.user_name, 'Jerry')

    def test_set_email(self):
        """Test setting a new email."""
        self.user.email = 'lee@example.com'
        self.assertEqual(self.user.email, 'lee@example.com')

    def test_set_invalid_email(self):
        """Test setting an invalid email and expect a ValueError."""
        with self.assertRaises(ValueError):
            self.user.email = 'invalid'

    def test_set_last_login_ip(self):
        """Test setting a new last login IP."""
        self.user.last_login_ip = '192.168.1.2'
        self.assertEqual(self.user.last_login_ip, '192.168.1.2')

    def test_set_invalid_last_login_ip(self):
        """Test setting an invalid last login IP and expect a ValueError."""
        with self.assertRaises(ValueError):
            self.user.last_login_ip = '192.invalid'

    def test_set_user_type(self):
        """Test setting a new user type."""
        self.user.user_type = 2
        self.assertEqual(self.user.user_type, 2)

    def test_set_invalid_user_type(self):
        """Test setting an invalid user type and expect a ValueError."""
        with self.assertRaises(ValueError):
            self.user.user_type = 4


class TestUserRepoMapper(unittest.TestCase):
    """
    This class tests the methods in UserRepoMapper class.
    This class inherits from the unittest.
    """

    def setUp(self):
        self.mapper = UserRepoMapper()

    def test_map_from_repo(self):
        """
        Test the map_from_repo method of the UserRepoMapper class.
        """
        record = {
            'uuid': 'some-uuid-for-test',
            'user_name': 'Jerry Li',
            'email': 'jerry.li@example.com',
            'last_login_ip': '192.168.1.1',
            'user_type': 1
        }
        user = self.mapper.map_from_repo(record)
        self.assertEqual(user.entity_uuid, 'some-uuid-for-test')
        self.assertEqual(user.user_name, 'Jerry Li')
        self.assertEqual(user.email, 'jerry.li@example.com')
        self.assertEqual(user.last_login_ip, '192.168.1.1')
        self.assertEqual(user.user_type, 1)

    def test_map_to_repo(self):
        """
        Test the map_to_repo method of the UserRepoMapper class.
        """
        user = User('other-uuid-for-test', 'Xu L',
                    'xul@google.com', '192.168.1.1', 1)
        record = self.mapper.map_to_repo(user)
        self.assertEqual(record['uuid'], 'other-uuid-for-test')
        self.assertEqual(record['user_name'], 'Xu L')
        self.assertEqual(record['email'], 'xul@google.com')
        self.assertEqual(record['last_login_ip'], '192.168.1.1')
        self.assertEqual(record['user_type'], 1)


class TestUserRepository(unittest.TestCase):
    """
    This class tests the methods in UserRepository class.
    This class inherits from the unittest.
    """

    def test_fetch_users_by_user_type(self):
        """
        Test the fetch_users_by_user_type method of the UserRepository class.
        """
        with mock.patch.object(UserRepository, 'create_connection') as mock_create_connection:
            # create mock
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {
                    'uuid': 'test-uuid-1',
                    'user_name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'last_login_ip': '192.168.1.1',
                    'user_type': 1
                },
                {
                    'uuid': 'test-uuid-2',
                    'user_name': 'Jane Doe',
                    'email': 'jane.doe@example.com',
                    'last_login_ip': '192.168.1.2',
                    'user_type': 1
                }
            ]

            # call method for testing
            user_repo = UserRepository()
            users = user_repo.fetch_users_by_user_type(1)

            # check whether important methods called and query is correct
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM user WHERE user_type = '1'")
            mock_cursor.fetchall.assert_called_once_with()

            # assertion
            self.assertEqual(len(users), 2)
            self.assertEqual(users[0].entity_uuid, 'test-uuid-1')
            self.assertEqual(users[0].user_name, 'John Doe')
            self.assertEqual(users[0].email, 'john.doe@example.com')
            self.assertEqual(users[0].last_login_ip, '192.168.1.1')
            self.assertEqual(users[0].user_type, 1)

            self.assertEqual(users[1].entity_uuid, 'test-uuid-2')
            self.assertEqual(users[1].user_name, 'Jane Doe')
            self.assertEqual(users[1].email, 'jane.doe@example.com')
            self.assertEqual(users[1].last_login_ip, '192.168.1.2')
            self.assertEqual(users[1].user_type, 1)


class TestRepository(unittest.TestCase):
    """
    This class tests the methods in Repository class.
    This class inherits from the unittest.
    """

    def setUp(self):
        """
        Set up the test environment by initializing a Repository instance.
        """
        self.repo = Repository('test_table', UserRepoMapper())

    def test_create_connection(self):
        """
        Test the create_connection method of the Repository class.
        """
        with mock.patch('sqlite3.connect') as mock_connect:
            self.repo.create_connection()
            mock_connect.assert_called_once_with('demo.db')

    def test_fetch_all(self):
        """
        Test the fetch_all method of the Repository class.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []

            self.repo.fetch_all()
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM test_table WHERE deleted = 0")
            mock_cursor.fetchall.assert_called_once_with()

    def test_fetch_all_include_deleted(self):
        """
        Test the fetch_all method of the Repository class with include_deleted parameter set to True.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []

            self.repo.fetch_all(include_deleted=True)
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM test_table")
            mock_cursor.fetchall.assert_called_once_with()

    def test_fetch_one_by_uuid(self):
        """
        Test the fetch_one_by_uuid method of the Repository class.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {
                'uuid': 'test-uuid',
                'user_name': 'John Doe',
                'email': 'john.doe@example.com',
                'last_login_ip': '192.168.1.1',
                'user_type': 1
            }

            result = self.repo.fetch_one_by_uuid('test-uuid')
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM test_table WHERE uuid = 'test-uuid'")
            mock_cursor.fetchone.assert_called_once_with()
            self.assertIsNotNone(result)

    def test_add_one(self):
        """
        Test the add_one method of the Repository class.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = None

            user = User('test-uuid', 'John Doe',
                        'john.doe@example.com', '192.168.1.1', 1)
            self.repo.add_one(user)
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once()
            mock_connection.commit.assert_called_once()

    def test_delete_one_by_uuid_with_existing_entity(self):
        """
        Test the delete_one_by_uuid method of the Repository class with an existing entity.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = User(
                'test-uuid', 'John Doe', 'john.doe@example.com', '192.168.1.1', 1)

            result = self.repo.delete_one_by_uuid('test-uuid')
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "DELETE FROM test_table Where uuid = 'test-uuid'")
            mock_connection.commit.assert_called_once()
            self.assertIsNotNone(result)

    def test_delete_one_by_uuid_with_non_existing_entity(self):
        """
        Test the delete_one_by_uuid method of the Repository class with a non-existing entity.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = None

            result = self.repo.delete_one_by_uuid('non-existing-uuid')
            mock_create_connection.assert_not_called()
            mock_cursor.execute.assert_not_called()
            mock_connection.commit.assert_not_called()
            self.assertIsNone(result)

    def test_soft_delete_one_by_uuid_with_existing_entity(self):
        """
        Test the soft_delete_one_by_uuid method of the Repository class with an existing entity.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = User(
                'test-uuid', 'John Doe', 'john.doe@example.com', '192.168.1.1', 1)

            result = self.repo.soft_delete_one_by_uuid('test-uuid')
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "UPDATE test_table SET deleted = 1 WHERE uuid = 'test-uuid'")
            mock_connection.commit.assert_called_once()
            self.assertIsNotNone(result)

    def test_soft_delete_one_by_uuid_with_non_existing_entity(self):
        """
        Test the soft_delete_one_by_uuid method of the Repository class with a non-existing entity.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = None

            result = self.repo.soft_delete_one_by_uuid('non-existing-uuid')
            mock_create_connection.assert_not_called()
            mock_cursor.execute.assert_not_called()
            mock_connection.commit.assert_not_called()
            self.assertIsNone(result)

    def test_update_one(self):
        """
        Test the update_one method of the Repository class.
        """
        with mock.patch.object(Repository, 'create_connection') as mock_create_connection, \
                mock.patch.object(Repository, 'fetch_one_by_uuid') as mock_fetch_one_by_uuid:
            mock_cursor = mock.MagicMock()
            mock_connection = mock.MagicMock()
            mock_create_connection.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_fetch_one_by_uuid.return_value = None

            user = User('test-uuid', 'John Doe',
                        'john.doe@example.com', '192.168.1.1', 1)
            self.repo.update_one(user)
            mock_create_connection.assert_called_once()
            mock_cursor.execute.assert_called_once()
            mock_connection.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
