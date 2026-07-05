package com.bfhs.parent.data.repository

import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.local.SchoolDao
import com.bfhs.parent.data.network.BfhsApiService
import com.bfhs.parent.domain.models.SchoolProfile
import com.bfhs.parent.domain.repository.SchoolRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SchoolRepositoryImpl @Inject constructor(
    private val api: BfhsApiService,
    private val schoolDao: SchoolDao
) : SchoolRepository {

    override fun schoolProfile(): Flow<Resource<SchoolProfile>> = flow {
        emit(Resource.Loading)
        val cached = schoolDao.observe().first()
        if (cached != null) emit(Resource.Success(cached.toDomain(), fromCache = true))
        try {
            val fresh = api.getSchoolProfile()
            schoolDao.insert(fresh.toEntity())
            schoolDao.observe().first()?.let { emit(Resource.Success(it.toDomain())) }
        } catch (e: Exception) {
            if (cached == null) emit(Resource.Error(e.userMessage()))
        }
    }
}
