package com.bfhs.parent.data.repository

import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.local.NotificationDao
import com.bfhs.parent.data.network.BfhsApiService
import com.bfhs.parent.domain.models.SchoolNotification
import com.bfhs.parent.domain.repository.NotificationRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationRepositoryImpl @Inject constructor(
    private val api: BfhsApiService,
    private val notificationDao: NotificationDao
) : NotificationRepository {

    override fun notifications(): Flow<Resource<List<SchoolNotification>>> = flow {
        emit(Resource.Loading)
        val cached = notificationDao.observeAll().first().map { it.toDomain() }
        if (cached.isNotEmpty()) emit(Resource.Success(cached, fromCache = true))
        try {
            val fresh = api.getNotifications()
            notificationDao.replaceAll(fresh.map { it.toEntity() })
            emit(Resource.Success(notificationDao.observeAll().first().map { it.toDomain() }))
        } catch (e: Exception) {
            if (cached.isEmpty()) emit(Resource.Error(e.userMessage()))
        }
    }

    override suspend fun markAllRead() = notificationDao.markAllRead()

    override fun hasUnread(): Flow<Boolean> =
        notificationDao.observeUnreadCount().map { it > 0 }
}
