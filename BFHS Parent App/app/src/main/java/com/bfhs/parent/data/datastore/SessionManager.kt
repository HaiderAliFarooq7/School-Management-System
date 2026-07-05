package com.bfhs.parent.data.datastore

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/** Persists the auth session (JWT + parent identity) and app preferences in DataStore. */
@Singleton
class SessionManager @Inject constructor(
    private val dataStore: DataStore<Preferences>
) {

    private object Keys {
        val TOKEN = stringPreferencesKey("jwt_token")
        val PARENT_NAME = stringPreferencesKey("parent_name")
        val MOBILE = stringPreferencesKey("mobile_number")
        val LANGUAGE = stringPreferencesKey("language")
    }

    val token: Flow<String?> = dataStore.data.map { it[Keys.TOKEN] }
    val parentName: Flow<String?> = dataStore.data.map { it[Keys.PARENT_NAME] }
    val mobileNumber: Flow<String?> = dataStore.data.map { it[Keys.MOBILE] }
    val language: Flow<String> = dataStore.data.map { it[Keys.LANGUAGE] ?: "en" }

    suspend fun tokenOnce(): String? = token.first()

    suspend fun saveSession(token: String, parentName: String, mobileNumber: String) {
        dataStore.edit {
            it[Keys.TOKEN] = token
            it[Keys.PARENT_NAME] = parentName
            it[Keys.MOBILE] = mobileNumber
        }
    }

    suspend fun setLanguage(tag: String) {
        dataStore.edit { it[Keys.LANGUAGE] = tag }
    }

    suspend fun clearSession() {
        dataStore.edit {
            it.remove(Keys.TOKEN)
            it.remove(Keys.PARENT_NAME)
            it.remove(Keys.MOBILE)
        }
    }
}
