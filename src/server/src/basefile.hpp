#include <cstdio>
#include <iostream>
#pragma once

class BaseFile {
private:
    FILE* file;
    const char* open_mode;

public:
    BaseFile();
    BaseFile(const char* filename, const char* mode);
    explicit BaseFile(FILE* fp);
    virtual ~BaseFile();

    //Запрещаем копирование
    BaseFile(const BaseFile&) = delete;
    BaseFile& operator=(const BaseFile&) = delete;

    //Разрешаем перемещение
    BaseFile(BaseFile&& other);
    BaseFile& operator=(BaseFile&& other);

    bool is_open() const;
    bool can_read() const;
    bool can_write() const;

    size_t write_raw(const void* buf, size_t n_bytes);
    size_t read_raw(void* buf, size_t n_bytes);

    virtual size_t write(const void* buf, size_t n_bytes);
    virtual size_t read(void* buf, size_t n_bytes);

    long tell() const;
    bool seek(long offset);
    bool close();
};