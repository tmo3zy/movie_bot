#include "basefile.hpp"
#include <cstring>

BaseFile::BaseFile() : file(nullptr), open_mode(nullptr){
}

BaseFile::BaseFile(const char* filename, const char* mode){
    if (filename && mode)
    {
        file = fopen(filename, mode);
        if (file)
        {
            open_mode = mode;
        }
    }
}

BaseFile::BaseFile(FILE* fp) : file(fp){
}

BaseFile::~BaseFile(){
    close();
}

bool BaseFile::is_open() const{
    return file != nullptr;
}

BaseFile::BaseFile(BaseFile&& other) : file(other.file), open_mode(other.open_mode) 
{
    other.file = nullptr;
    other.open_mode = nullptr;
}

BaseFile& BaseFile::operator=(BaseFile&& other){
    if (this != &other) {
        close();
        file = other.file;
        open_mode = other.open_mode;
        other.file = nullptr;
        other.open_mode = nullptr;
    }
    return *this;
}

bool BaseFile::can_read() const{
    if (!is_open())
    {
        return false;
    }
    return strchr(open_mode, 'r') != nullptr || strchr(open_mode, '+') != nullptr;
}

bool BaseFile::can_write() const{
    if (!is_open())
    {
        return false;
    }
    
    if (open_mode)
    {
        return strchr(open_mode, 'w') != nullptr || strchr(open_mode, 'b') != nullptr || strchr(open_mode, '+') != nullptr;
    }
    
    return false;
}

size_t BaseFile::write_raw(const void* buf, size_t n_bytes){
    if (!can_write() || n_bytes == 0 || (n_bytes > 0 && buf == nullptr))
    {
        return 0;
    }

    return fwrite(buf, 1, n_bytes, file);
}

size_t BaseFile::read_raw(void* buf, size_t n_bytes){
    if (!can_read() || (n_bytes > 0 && buf == nullptr) || n_bytes == 0)
    {
        return 0;
    }
    
    return fread(buf, 1, n_bytes, file);
}

size_t BaseFile::write(const void* buf, size_t n_bytes){
    if (!can_write() || n_bytes == 0 || (n_bytes > 0 && buf == nullptr))
    {
        return 0;
    }

    return fwrite(buf, 1, n_bytes, file);
}

size_t BaseFile::read(void* buf, size_t n_bytes){
    if (!can_read() || (n_bytes == 0 && buf != nullptr) || n_bytes == 0)
    {
        return 0;
    }
    
    return fread(buf, 1, n_bytes, file);
}

long BaseFile::tell() const{
    if (!is_open())
    {
        return -1L;
    }

    return ftell(file);
}

bool BaseFile::seek(long offset){
    if (!is_open() || offset < 0 || fseek(file, offset, SEEK_SET) != 0)
    {
        return false;
    }
    return true;
}

bool BaseFile::close() {
    if (file != nullptr) {
        int result = fclose(file);
        file = nullptr;
        return result == 0;
    }
    return false;
}